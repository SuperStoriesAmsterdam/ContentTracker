"""
SuperStories Content Engine v4
Flask application for content intelligence and strategy
Uses Claude for extraction and strategy recommendations
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf.csrf import CSRFProtect

from config import Config
from models.database import init_db, get_db_path
from models.client import Client
from models.brief import Brief
from models.content import Content
from models.derived_content import DerivedContent
from models.ad_spend import AdSpend, PLATFORMS, CURRENCIES, MONTH_NAMES
from models.site import Site
from models.keyword_target import KeywordTarget
from models.gsc_snapshot import GscSnapshot
from migrations import run_migrations
from services.claude_service import ClaudeService
from services.seo_validator import SEOValidator
from services.schema_generator import SchemaGenerator
from services.content_parser import ContentParser
from services.google_docs_service import GoogleDocsService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
csrf = CSRFProtect(app)

# Initialize database and run migrations
init_db()
run_migrations(get_db_path())

# Initialize services
claude_service = ClaudeService()
content_parser = ContentParser()

# Google Docs service is optional (requires OAuth credentials)
google_docs_service = None
if Config.GOOGLE_CLIENT_ID and Config.GOOGLE_CLIENT_SECRET:
    google_docs_service = GoogleDocsService()


# ==================== HELPER FUNCTIONS ====================

def safe_int(value, default=0):
    """Safely convert to int with fallback."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_list_from_textarea(value):
    """Convert newline-separated textarea to list."""
    if not value:
        return []
    return [item.strip() for item in value.split('\n') if item.strip()]

def get_current_client():
    """Get the current client from session."""
    client_id = session.get('client_id')
    if not client_id:
        return None
    return Client.get_by_id(client_id)

def get_google_credentials():
    """Get Google credentials — checks session first, falls back to DB, re-caches in session."""
    creds = session.get('google_credentials')
    if creds:
        return creds

    client = get_current_client()
    if client and client.google_credentials:
        try:
            creds = json.loads(client.google_credentials)
            session['google_credentials'] = creds
            return creds
        except (json.JSONDecodeError, TypeError):
            pass

    return None

def require_client(f):
    """Decorator to require client login."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('client_id'):
            flash('Please select a client first.', 'warning')
            return redirect(url_for('dashboard'))
        client = Client.get_by_id(session['client_id'])
        if not client:
            session.pop('client_id', None)
            session.pop('client_name', None)
            flash('Client not found. Please select a client.', 'warning')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== DASHBOARD ROUTES ====================

@app.route('/')
def dashboard():
    """Home page — hero + sign in."""
    if session.get('client_id'):
        return redirect(url_for('workspace'))
    return render_template('dashboard.html')

@app.route('/clients')
def clients_page():
    """Client selection page."""
    clients = Client.get_all()
    return render_template('clients.html', clients=clients)

@app.route('/how')
def manual():
    """HOW — how the tool works."""
    return render_template('manual.html')

@app.route('/why')
def seo_guide():
    """WHY — the technical aspects of contemporary content marketing."""
    return render_template('seo_guide.html')

@app.route('/client/new', methods=['GET', 'POST'])
def create_client():
    """Create a new client."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()

        if not name:
            flash('Client name is required.', 'error')
            return redirect(url_for('create_client'))

        if Client.get_by_name(name):
            flash('A client with this name already exists.', 'error')
            return redirect(url_for('create_client'))

        client = Client(name=name)
        client.save()
        
        session['client_id'] = client.id
        session['client_name'] = client.name
        flash(f'Client "{name}" created!', 'success')
        return redirect(url_for('workspace'))

    return render_template('client_form.html')

@app.route('/client/login', methods=['POST'])
def login_client():
    """Login to existing client."""
    client_id = request.form.get('client_id')

    client = Client.get_by_id(client_id)
    if not client:
        flash('Client not found.', 'error')
        return redirect(url_for('clients_page'))
    
    session['client_id'] = client.id
    session['client_name'] = client.name
    return redirect(url_for('workspace'))

@app.route('/client/logout')
def logout_client():
    """Logout from client."""
    session.pop('client_id', None)
    session.pop('client_name', None)
    return redirect(url_for('dashboard'))


# ==================== WORKSPACE ROUTES ====================

@app.route('/workspace')
@require_client
def workspace():
    """Client workspace - main content hub."""
    client = get_current_client()
    briefs = Brief.get_by_client(client.id)
    contents = Content.get_by_client(client.id, limit=10)

    return render_template('workspace.html',
                         client=client,
                         briefs=briefs,
                         contents=contents)

@app.route('/client/settings', methods=['GET', 'POST'])
@require_client
def client_settings():
    """Edit client settings."""
    client = get_current_client()
    
    if request.method == 'POST':
        client.name = request.form.get('name', client.name).strip()
        client.author_name = request.form.get('author_name', '').strip() or None
        client.tone = request.form.get('tone', '').strip()
        client.key_phrases = safe_list_from_textarea(request.form.get('key_phrases', ''))
        client.forbidden_words = safe_list_from_textarea(request.form.get('forbidden_words', ''))
        client.target_audience = request.form.get('target_audience', '').strip()
        client.entity_statement = request.form.get('entity_statement', '').strip()
        client.core_keywords = safe_list_from_textarea(request.form.get('core_keywords', ''))
        client.competitive_differentiation = request.form.get('competitive_differentiation', '').strip()
        client.linkedin_guidelines = request.form.get('linkedin_guidelines', '').strip()
        client.instagram_guidelines = request.form.get('instagram_guidelines', '').strip()
        client.is_thought_leadership = 'is_thought_leadership' in request.form
        
        client.save()
        flash('Settings saved.', 'success')
        return redirect(url_for('workspace'))
    
    return render_template('client_settings.html', client=client)


# ==================== BRIEF ROUTES ====================

@app.route('/briefs')
@require_client
def briefs_list():
    """List all briefs."""
    client = get_current_client()
    briefs = Brief.get_by_client(client.id)
    return render_template('briefs_list.html', client=client, briefs=briefs)

@app.route('/brief/new', methods=['GET', 'POST'])
@require_client
def create_brief():
    """Create a new content brief."""
    client = get_current_client()

    if request.method == 'POST':
        content_track = request.form.get('content_track', 'seo')

        brief = Brief(
            client_id=client.id,
            title=request.form.get('title', '').strip(),
            content_type=request.form.get('content_type'),
            content_track=content_track,
            language=request.form.get('language', 'nl'),
            target_icp=request.form.get('target_icp', '').strip(),
            must_include=safe_list_from_textarea(request.form.get('must_include', '')),
            must_avoid=safe_list_from_textarea(request.form.get('must_avoid', '')),
            special_instructions=request.form.get('special_instructions', '').strip()
        )

        # SEO-specific fields
        if content_track == 'seo':
            brief.primary_keyword = request.form.get('primary_keyword', '').strip()
            brief.secondary_keywords = safe_list_from_textarea(request.form.get('secondary_keywords', ''))
            brief.answer_target = request.form.get('answer_target', '').strip()
            brief.search_intent = request.form.get('search_intent')
            brief.word_count_target = safe_int(request.form.get('word_count_target'), 1500)
            brief.cta = request.form.get('cta', '').strip()

        # Thought leadership-specific fields
        if content_track == 'thought_leadership':
            brief.core_thesis = request.form.get('core_thesis', '').strip()
            brief.contrarian_angle = request.form.get('contrarian_angle', '').strip()
            brief.personal_story_prompt = request.form.get('personal_story_prompt', '').strip()
            brief.emotional_intent = request.form.get('emotional_intent')
            brief.call_to_think = request.form.get('call_to_think', '').strip()

        if not brief.title:
            flash('Title is required.', 'error')
            return render_template('brief_form.html',
                                 client=client,
                                 brief=None,
                                 content_types=Brief.CONTENT_TYPES,
                                 content_tracks=Brief.CONTENT_TRACKS,
                                 languages=Brief.LANGUAGES,
                                 search_intents=Brief.SEARCH_INTENTS,
                                 emotional_intents=Brief.EMOTIONAL_INTENTS)

        brief.save()
        flash('Brief created.', 'success')
        return redirect(url_for('briefs_list'))

    prefill_keyword = request.args.get('keyword', '')
    return render_template('brief_form.html',
                         client=client,
                         brief=None,
                         prefill_keyword=prefill_keyword,
                         content_types=Brief.CONTENT_TYPES,
                         content_tracks=Brief.CONTENT_TRACKS,
                         languages=Brief.LANGUAGES,
                         search_intents=Brief.SEARCH_INTENTS,
                         emotional_intents=Brief.EMOTIONAL_INTENTS)

@app.route('/brief/<int:brief_id>/edit', methods=['GET', 'POST'])
@require_client
def edit_brief(brief_id):
    """Edit an existing brief."""
    client = get_current_client()
    brief = Brief.get_by_id(brief_id)

    if not brief or brief.client_id != client.id:
        flash('Brief not found.', 'error')
        return redirect(url_for('briefs_list'))

    if request.method == 'POST':
        content_track = request.form.get('content_track', 'seo')

        brief.title = request.form.get('title', brief.title).strip()
        brief.content_type = request.form.get('content_type', brief.content_type)
        brief.content_track = content_track
        brief.language = request.form.get('language', brief.language)
        brief.target_icp = request.form.get('target_icp', '').strip()
        brief.must_include = safe_list_from_textarea(request.form.get('must_include', ''))
        brief.must_avoid = safe_list_from_textarea(request.form.get('must_avoid', ''))
        brief.special_instructions = request.form.get('special_instructions', '').strip()

        # SEO-specific fields
        if content_track == 'seo':
            brief.primary_keyword = request.form.get('primary_keyword', '').strip()
            brief.secondary_keywords = safe_list_from_textarea(request.form.get('secondary_keywords', ''))
            brief.answer_target = request.form.get('answer_target', '').strip()
            brief.search_intent = request.form.get('search_intent')
            brief.word_count_target = safe_int(request.form.get('word_count_target'), 1500)
            brief.cta = request.form.get('cta', '').strip()

        # Thought leadership-specific fields
        if content_track == 'thought_leadership':
            brief.core_thesis = request.form.get('core_thesis', '').strip()
            brief.contrarian_angle = request.form.get('contrarian_angle', '').strip()
            brief.personal_story_prompt = request.form.get('personal_story_prompt', '').strip()
            brief.emotional_intent = request.form.get('emotional_intent')
            brief.call_to_think = request.form.get('call_to_think', '').strip()

        brief.save()
        flash('Brief updated.', 'success')
        return redirect(url_for('briefs_list'))

    return render_template('brief_form.html',
                         client=client,
                         brief=brief,
                         content_types=Brief.CONTENT_TYPES,
                         content_tracks=Brief.CONTENT_TRACKS,
                         languages=Brief.LANGUAGES,
                         search_intents=Brief.SEARCH_INTENTS,
                         emotional_intents=Brief.EMOTIONAL_INTENTS)

@app.route('/brief/<int:brief_id>/delete', methods=['POST'])
@require_client
def delete_brief(brief_id):
    """Delete a brief."""
    client = get_current_client()
    brief = Brief.get_by_id(brief_id)
    
    if not brief or brief.client_id != client.id:
        flash('Brief not found.', 'error')
        return redirect(url_for('briefs_list'))
    
    brief.delete()
    flash('Brief deleted.', 'success')
    return redirect(url_for('briefs_list'))


@app.route('/content/<int:content_id>')
@require_client
def view_content(content_id):
    """View generated content with SEO checks."""
    client = get_current_client()
    content = Content.get_by_id(content_id)
    
    if not content or content.client_id != client.id:
        flash('Content not found.', 'error')
        return redirect(url_for('workspace'))
    
    brief = Brief.get_by_id(content.brief_id)
    
    # Run SEO checks (only for SEO content)
    seo_checks = {}
    if brief and (brief.content_track == 'seo' or not brief.content_track):
        seo_checks = SEOValidator.run_all_checks(content, brief, client)

    # Get derived content
    derived = DerivedContent.get_by_source(content_id)

    # Fetch GSC performance data if published_url is set
    search_performance = None
    if content.published_url and client.search_console_site and google_docs_service:
        # Check cache — use 6-hour TTL
        should_fetch = True
        if content.search_console_data and content.last_performance_fetch:
            try:
                last_fetch = datetime.fromisoformat(content.last_performance_fetch)
                if datetime.now() - last_fetch < timedelta(hours=6):
                    search_performance = json.loads(content.search_console_data)
                    should_fetch = False
            except (ValueError, json.JSONDecodeError):
                pass

        if should_fetch:
            creds = get_google_credentials()
            if creds:
                try:
                    search_performance = google_docs_service.get_search_performance(
                        creds, client.search_console_site, url_filter=content.published_url
                    )
                    content.search_console_data = json.dumps(search_performance)
                    content.last_performance_fetch = datetime.now().isoformat()
                    content.save()
                except Exception as e:
                    logger.warning(f"Failed to fetch GSC data for content {content_id}: {e}")

    return render_template('view_content.html',
                         client=client,
                         content=content,
                         brief=brief,
                         seo_checks=seo_checks,
                         derived_content=derived,
                         search_performance=search_performance)

@app.route('/content/<int:content_id>/delete', methods=['POST'])
@require_client
def delete_content(content_id):
    """Delete generated content."""
    client = get_current_client()
    content = Content.get_by_id(content_id)
    
    if not content or content.client_id != client.id:
        flash('Content not found.', 'error')
        return redirect(url_for('workspace'))
    
    content.delete()
    flash('Content deleted.', 'success')
    return redirect(url_for('workspace'))


# ==================== PUBLISHED URL ROUTE ====================

@app.route('/content/<int:content_id>/set-url', methods=['POST'])
@require_client
def set_published_url(content_id):
    """Set or remove published URL on content."""
    client = get_current_client()
    content = Content.get_by_id(content_id)

    if not content or content.client_id != client.id:
        flash('Content not found.', 'error')
        return redirect(url_for('workspace'))

    url = request.form.get('published_url', '').strip()
    if request.form.get('remove_url'):
        content.published_url = None
        content.search_console_data = None
        content.last_performance_fetch = None
        flash('Published URL removed.', 'success')
    elif url:
        content.published_url = url
        flash('Published URL saved.', 'success')
    else:
        flash('Please enter a URL.', 'warning')

    content.save()
    return redirect(url_for('view_content', content_id=content.id))


# ==================== SOCIAL CONTENT ROUTES ====================

@app.route('/content/<int:content_id>/derive', methods=['GET', 'POST'])
@require_client
def derive_social(content_id):
    """Derive social media posts from content."""
    client = get_current_client()
    content = Content.get_by_id(content_id)
    
    if not content or content.client_id != client.id:
        flash('Content not found.', 'error')
        return redirect(url_for('workspace'))
    
    if request.method == 'POST':
        platform = request.form.get('platform', 'linkedin')
        
        try:
            post_content = claude_service.generate_social_post(
                content=content,
                client=client,
                platform=platform
            )
            
            derived = DerivedContent(
                source_content_id=content.id,
                client_id=client.id,
                platform=platform,
                content=post_content
            )
            derived.save()
            
            flash(f'{platform.title()} post created!', 'success')
            return redirect(url_for('view_content', content_id=content.id))
            
        except Exception as e:
            logger.error(f"Social generation error: {e}")
            flash(f'Generation failed: {str(e)}', 'error')
    
    existing_derived = DerivedContent.get_by_source(content_id)
    return render_template('derive_social.html',
                         client=client,
                         content=content,
                         derived_content=existing_derived,
                         platforms=DerivedContent.PLATFORMS)


# ==================== GOOGLE OAUTH ROUTES ====================

@app.route('/google/connect')
def google_connect():
    """Start Google OAuth flow."""
    if not google_docs_service:
        flash('Google integration is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.', 'warning')
        return redirect(request.referrer or url_for('dashboard'))

    redirect_after = request.args.get('redirect', url_for('dashboard'))
    session['oauth_redirect'] = redirect_after

    auth_url, state, code_verifier = google_docs_service.get_authorization_url()
    session['oauth_state'] = state
    session['oauth_code_verifier'] = code_verifier

    return redirect(auth_url)

@app.route('/oauth/callback')
def oauth_callback():
    """Handle OAuth callback from Google."""
    if request.args.get('state') != session.get('oauth_state'):
        flash('OAuth state mismatch. Please try again.', 'error')
        return redirect(url_for('dashboard'))
    
    if 'error' in request.args:
        flash(f"Google auth error: {request.args.get('error')}", 'error')
        return redirect(url_for('dashboard'))
    
    code = request.args.get('code')
    try:
        code_verifier = session.pop('oauth_code_verifier', None)
        creds = google_docs_service.exchange_code(code, code_verifier)
        session['google_credentials'] = creds

        # Persist credentials to database so they survive restarts
        client = get_current_client()
        if client:
            client.google_credentials = json.dumps(creds)
            client.save()

        flash('Google account connected!', 'success')
    except Exception as e:
        flash(f'Failed to connect Google: {str(e)}', 'error')

    redirect_url = session.pop('oauth_redirect', url_for('dashboard'))
    return redirect(redirect_url)

@app.route('/google/disconnect')
def google_disconnect():
    """Disconnect Google account."""
    session.pop('google_credentials', None)

    # Clear from database too
    client = get_current_client()
    if client:
        client.google_credentials = None
        client.save()

    flash('Google account disconnected.', 'success')
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/content/<int:content_id>/export-google')
@require_client
def export_to_google(content_id):
    """Export content to Google Docs."""
    content = Content.get_by_id(content_id)
    if not content:
        flash('Content not found.', 'error')
        return redirect(url_for('dashboard'))
    
    creds = get_google_credentials()
    if not creds:
        return redirect(url_for('google_connect',
                                redirect=url_for('export_to_google', content_id=content_id)))
    
    try:
        doc_id, doc_url = google_docs_service.create_document_formatted(
            creds_dict=creds,
            title=content.meta_title or f"Content {content.id}",
            meta_title=content.meta_title or "",
            meta_description=content.meta_description or "",
            body_content=content.body or ""
        )
        
        content.google_doc_id = doc_id
        content.google_doc_url = doc_url
        content.save()
        
        flash('Exported to Google Docs!', 'success')
        return redirect(doc_url)
        
    except Exception as e:
        if 'invalid_grant' in str(e) or 'expired' in str(e).lower():
            session.pop('google_credentials', None)
            flash('Google session expired. Please reconnect.', 'error')
            return redirect(url_for('google_connect',
                                    redirect=url_for('export_to_google', content_id=content_id)))
        
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('view_content', content_id=content_id))


# ==================== SEARCH CONSOLE ROUTES ====================

@app.route('/search-console')
@require_client
def search_console_dashboard():
    """Search Console data dashboard."""
    client = get_current_client()

    creds = get_google_credentials()
    if not creds:
        return redirect(url_for('google_connect',
                                redirect=url_for('search_console_dashboard')))
    
    try:
        sites = google_docs_service.get_search_console_sites(creds)
        site_url = client.search_console_site
        performance = None
        pages = None
        opportunities = None

        if site_url and site_url in sites:
            performance = google_docs_service.get_search_performance(creds, site_url)
            pages = google_docs_service.get_page_performance(creds, site_url)
            opportunities = google_docs_service.get_keyword_opportunities(creds, site_url)

        # Get keyword targets and update their GSC status
        keyword_targets = KeywordTarget.get_by_client(client.id)
        if performance and keyword_targets:
            for target in keyword_targets:
                target.update_from_gsc(performance.get('rows', []))

        return render_template('search_console.html',
                             client=client,
                             sites=sites,
                             selected_site=site_url,
                             performance=performance,
                             pages=pages,
                             opportunities=opportunities,
                             keyword_targets=keyword_targets)

    except Exception as e:
        flash(f'Error loading Search Console: {str(e)}', 'error')
        return redirect(url_for('workspace'))

@app.route('/search-console/set-site', methods=['POST'])
@require_client
def set_search_console_site():
    """Set Search Console site for client."""
    client = get_current_client()
    site_url = request.form.get('site_url')
    client.search_console_site = site_url
    client.save()
    flash('Search Console site configured.', 'success')
    return redirect(url_for('search_console_dashboard'))


# ==================== KEYWORD TARGETING ROUTES ====================

@app.route('/search-console/keywords/add', methods=['POST'])
@require_client
def add_keyword_target():
    """Add a target keyword for tracking."""
    client = get_current_client()
    keyword = request.form.get('keyword', '').strip()
    zone = int(request.form.get('zone', 3))
    notes = request.form.get('notes', '').strip()

    if not keyword:
        flash('Keyword is required.', 'error')
        return redirect(url_for('search_console_dashboard'))

    target = KeywordTarget(
        client_id=client.id,
        keyword=keyword,
        zone=max(1, min(3, zone)),
        notes=notes
    )
    target.save()
    flash(f'Target keyword "{keyword}" added (Zone {zone}).', 'success')
    return redirect(url_for('search_console_dashboard'))


@app.route('/search-console/keywords/<int:target_id>/delete', methods=['POST'])
@require_client
def delete_keyword_target(target_id):
    """Delete a target keyword."""
    client = get_current_client()
    target = KeywordTarget.get_by_id(target_id)

    if not target or target.client_id != client.id:
        flash('Target keyword not found.', 'error')
        return redirect(url_for('search_console_dashboard'))

    target.delete()
    flash('Target keyword removed.', 'success')
    return redirect(url_for('search_console_dashboard'))


@app.route('/search-console/snapshot', methods=['POST'])
@require_client
def take_gsc_snapshot():
    """Take a snapshot of current GSC data for historical tracking."""
    client = get_current_client()
    creds = get_google_credentials()

    if not creds or not client.search_console_site:
        flash('Connect Google and select a site first.', 'error')
        return redirect(url_for('search_console_dashboard'))

    try:
        performance = google_docs_service.get_search_performance(
            creds, client.search_console_site, days=28)
        rows = performance.get('rows', [])
        count = GscSnapshot.take_snapshot(client.id, client.search_console_site, rows)

        if count > 0:
            flash(f'Snapshot saved — {count} keywords recorded.', 'success')
        else:
            flash('Snapshot already taken today.', 'info')
    except Exception as e:
        flash(f'Snapshot failed: {str(e)}', 'error')

    return redirect(url_for('search_console_dashboard'))


@app.route('/search-console/trajectory/<path:keyword>')
@require_client
def keyword_trajectory(keyword):
    """Get trajectory data for a keyword (JSON for charts)."""
    client = get_current_client()
    data = GscSnapshot.get_trajectory(client.id, keyword)
    return jsonify(data)


# ==================== ANALYTICS ROUTES ====================

@app.route('/analytics')
@require_client
def analytics_dashboard():
    """Analytics data dashboard."""
    client = get_current_client()

    creds = get_google_credentials()
    if not creds:
        return redirect(url_for('google_connect',
                                redirect=url_for('analytics_dashboard')))
    
    try:
        properties = google_docs_service.get_analytics_accounts(creds)
        property_id = client.analytics_property_id
        pageviews = None
        
        conversions = None
        if property_id:
            pageviews = google_docs_service.get_analytics_pageviews(creds, property_id)
            conversions = google_docs_service.get_analytics_conversions(creds, property_id)

        return render_template('analytics.html',
                             client=client,
                             properties=properties,
                             selected_property=property_id,
                             pageviews=pageviews,
                             conversions=conversions)
    
    except Exception as e:
        flash(f'Error loading Analytics: {str(e)}', 'error')
        return redirect(url_for('workspace'))

@app.route('/analytics/set-property', methods=['POST'])
@require_client
def set_analytics_property():
    """Set Analytics property for client."""
    client = get_current_client()
    property_id = request.form.get('property_id')
    client.analytics_property_id = property_id
    client.save()
    flash('Analytics property configured.', 'success')
    return redirect(url_for('analytics_dashboard'))


# ==================== CONTENT STRATEGY ROUTES ====================

def _generate_strategy_recommendations(client, performance, opportunities, pages, existing_content):
    """Use Claude to generate content strategy recommendations based on GSC data."""
    # Format existing content titles
    content_titles = [c.meta_title or c.h1 or 'Untitled' for c in existing_content[:20]]

    prompt = f"""You are a content strategist analyzing Google Search Console data for "{client.name}".

Based on the data below, recommend exactly 5 new content pieces to create. Focus on:
1. Keywords with high impressions but low clicks (CTR optimization)
2. Keywords in positions 5-20 (low-hanging fruit to push to page 1)
3. Content gaps — topics their audience searches for but they haven't covered
4. Opportunities to create supporting/cluster content around strong performers

## Current Search Performance (Top Queries):
{json.dumps(performance.get('rows', [])[:15], indent=2) if performance else 'No data available'}

## Keyword Opportunities (Positions 5-20):
{json.dumps(opportunities[:10], indent=2) if opportunities else 'No opportunities found'}

## Top Pages:
{json.dumps(pages[:10], indent=2) if pages else 'No page data'}

## Existing Content Already Created:
{json.dumps(content_titles, indent=2)}

## Client Info:
- Target Audience: {client.target_audience or 'Not specified'}
- Core Keywords: {', '.join(client.core_keywords) if client.core_keywords else 'Not specified'}
- Competitive Differentiation: {client.competitive_differentiation or 'Not specified'}

Return a JSON array of exactly 5 recommendations. Each should have:
- "title": suggested article title
- "keyword": primary keyword to target
- "reasoning": 1-2 sentences explaining why this is a good opportunity
- "priority": "high", "medium", or "low"
- "type": one of "new_content", "optimize_existing", "supporting_cluster", "ctr_optimization"

Return ONLY the JSON array, no other text."""

    try:
        from anthropic import Anthropic
        anthropic_client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        response = anthropic_client.messages.create(
            model=Config.CLAUDE_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        result_text = response.content[0].text.strip()
        # Extract JSON from response (handle markdown code blocks)
        if result_text.startswith('```'):
            result_text = result_text.split('\n', 1)[1].rsplit('```', 1)[0].strip()
        return json.loads(result_text)
    except Exception as e:
        logger.error(f"Strategy recommendation error: {e}")
        return []


@app.route('/content-strategy')
@require_client
def content_strategy():
    """Content Strategy page with AI-powered recommendations."""
    client = get_current_client()

    creds = get_google_credentials()
    performance = None
    opportunities = None
    pages = None
    recommendations = []
    has_gsc = False

    if creds and client.search_console_site and google_docs_service:
        has_gsc = True
        try:
            performance = google_docs_service.get_search_performance(creds, client.search_console_site)
            opportunities = google_docs_service.get_keyword_opportunities(creds, client.search_console_site)
            pages = google_docs_service.get_page_performance(creds, client.search_console_site)
        except Exception as e:
            logger.warning(f"Failed to fetch GSC data for strategy: {e}")
            flash(f'Could not load Search Console data: {str(e)}', 'warning')

    existing_content = Content.get_by_client(client.id, limit=20)

    # Generate AI recommendations if we have any data to work with
    if performance or opportunities or existing_content:
        recommendations = _generate_strategy_recommendations(
            client, performance or {}, opportunities or [], pages or [], existing_content
        )

    return render_template('content_strategy.html',
                         client=client,
                         has_gsc=has_gsc,
                         performance=performance,
                         opportunities=opportunities,
                         recommendations=recommendations,
                         existing_content=existing_content)


# ==================== AD SPEND ROUTES ====================

@app.route('/ad-spend')
@require_client
def ad_spend():
    """View and manage monthly advertising spend."""
    client = get_current_client()
    entries = AdSpend.get_by_client(client.id)
    monthly_totals = AdSpend.get_monthly_totals(client.id)

    # Build a lookup dict of monthly totals keyed by (year, month)
    # for use in the GSC comparison table
    totals_by_month = {
        (row['year'], row['month']): row['total']
        for row in monthly_totals
    }

    return render_template('ad_spend.html',
                           client=client,
                           entries=entries,
                           monthly_totals=monthly_totals,
                           totals_by_month=totals_by_month,
                           platforms=PLATFORMS,
                           currencies=CURRENCIES,
                           month_names=MONTH_NAMES,
                           now=datetime.now())


@app.route('/ad-spend/add', methods=['POST'])
@require_client
def ad_spend_add():
    """Add a new monthly spend entry."""
    client = get_current_client()

    year = safe_int(request.form.get('year'))
    month = safe_int(request.form.get('month'))
    platform = request.form.get('platform', '').strip()
    currency = request.form.get('currency', 'EUR').strip()
    notes = request.form.get('notes', '').strip() or None

    try:
        amount = float(request.form.get('amount', 0))
    except ValueError:
        flash('Amount must be a number.', 'error')
        return redirect(url_for('ad_spend'))

    if not year or not month or not platform or amount <= 0:
        flash('Year, month, platform, and a positive amount are all required.', 'error')
        return redirect(url_for('ad_spend'))

    if platform not in PLATFORMS:
        flash('Invalid platform.', 'error')
        return redirect(url_for('ad_spend'))

    if currency not in CURRENCIES:
        flash('Invalid currency.', 'error')
        return redirect(url_for('ad_spend'))

    entry = AdSpend(
        client_id=client.id,
        year=year,
        month=month,
        platform=platform,
        amount=amount,
        currency=currency,
        notes=notes
    )
    entry.save()

    flash(f'Spend entry added: {platform} {currency} {amount:,.2f} for {MONTH_NAMES.get(month, month)} {year}.', 'success')
    return redirect(url_for('ad_spend'))


@app.route('/ad-spend/<int:spend_id>/delete', methods=['POST'])
@require_client
def ad_spend_delete(spend_id):
    """Delete a spend entry."""
    client = get_current_client()
    entry = AdSpend.get_by_id(spend_id)

    if not entry or entry.client_id != client.id:
        flash('Entry not found.', 'error')
        return redirect(url_for('ad_spend'))

    entry.delete()
    flash('Spend entry deleted.', 'success')
    return redirect(url_for('ad_spend'))


# ==================== MULTI-SITE ROUTES ====================

@app.route('/sites')
@require_client
def sites_list():
    """List all sites for the current client."""
    client = get_current_client()
    sites = Site.get_all_by_client_id(client.id)
    return render_template('sites_list.html', client=client, sites=sites)


@app.route('/sites/add', methods=['GET', 'POST'])
@require_client
def site_add():
    """Add a new site for the current client."""
    client = get_current_client()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        url = request.form.get('url', '').strip()
        gsc_property = request.form.get('gsc_property', '').strip()

        if not url:
            flash('URL is required.', 'error')
            return render_template('site_add.html', client=client)

        site = Site(client_id=client.id, url=url, name=name or None,
                    gsc_property=gsc_property or None)
        site.save()
        flash(f'Site "{name or url}" added.', 'success')
        return redirect(url_for('sites_list'))

    return render_template('site_add.html', client=client)


@app.route('/sites/<int:site_id>/delete', methods=['POST'])
@require_client
def site_delete(site_id):
    """Remove a site."""
    client = get_current_client()
    site = Site.get_by_id(site_id)

    if not site or site.client_id != client.id:
        flash('Site not found.', 'error')
        return redirect(url_for('sites_list'))

    site.delete()
    flash('Site removed.', 'success')
    return redirect(url_for('sites_list'))


@app.route('/dashboard/multi-site')
@require_client
def multi_site_dashboard():
    """
    Combined multi-site GSC performance dashboard.
    Shows all sites for the current client in a tab-based view.
    Falls back to client.search_console_site if no sites in the sites table.
    """
    client = get_current_client()

    creds = get_google_credentials()
    if not creds:
        return redirect(url_for('google_connect',
                                redirect=url_for('multi_site_dashboard')))

    days = safe_int(request.args.get('days'), 28)
    if days not in (7, 28, 90):
        days = 28

    sites = Site.get_all_by_client_id(client.id)

    # Backwards compatibility: if no sites in the table, use client.search_console_site
    if not sites and client.search_console_site:
        sites = [Site(
            id=0,
            client_id=client.id,
            url=client.search_console_site,
            name=client.search_console_site,
            gsc_property=client.search_console_site
        )]

    site_data = []
    for site in sites:
        entry = {
            'site': site,
            'performance': None,
            'pages': None,
            'error': None
        }

        if site.gsc_property:
            try:
                entry['performance'] = google_docs_service.get_search_performance(
                    creds, site.gsc_property, days=days
                )
                entry['pages'] = google_docs_service.get_page_performance(
                    creds, site.gsc_property, days=days
                )
            except Exception as e:
                logger.warning(f"GSC fetch failed for {site.gsc_property}: {e}")
                entry['error'] = str(e)

        site_data.append(entry)

    # Build "All Sites" summary: aggregate totals per site
    summary = []
    for entry in site_data:
        perf = entry['performance']
        row = {
            'name': entry['site'].name or entry['site'].url,
            'clicks': 0,
            'impressions': 0,
            'position': 0
        }
        if perf and perf.get('totals'):
            row['clicks'] = perf['totals'].get('clicks', 0)
            row['impressions'] = perf['totals'].get('impressions', 0)
        if perf and perf.get('rows'):
            positions = [r.get('position', 0) for r in perf['rows'] if r.get('position')]
            row['position'] = round(sum(positions) / len(positions), 1) if positions else 0
        summary.append(row)

    summary.sort(key=lambda r: r['clicks'], reverse=True)

    return render_template('dashboard_multi_site.html',
                           client=client,
                           site_data=site_data,
                           summary=summary,
                           days=days,
                           has_sites=bool(Site.get_all_by_client_id(client.id)))


# ==================== MAIN ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
