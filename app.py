"""
SuperStories Content Engine v4
Flask application for content intelligence and strategy
Uses Claude for extraction and strategy recommendations
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response, abort
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
from services import exporter

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


# ==================== SITE AUTH ====================

SITE_PASSWORD = os.environ.get('SITE_PASSWORD', '')
API_KEY = os.environ.get('CT_API_KEY', '')
PUBLIC_ROUTES = {'manual', 'seo_guide', 'site_login', 'static', 'google_connect', 'oauth_callback'}

@app.before_request
def check_site_auth():
    """Require site password for all routes except /how, /why, login, and API calls."""
    # API key auth — skip site password for API requests
    if request.path.startswith('/api/') and API_KEY:
        api_key = request.headers.get('X-API-Key', '')
        if api_key == API_KEY:
            return
        return jsonify({'error': 'Invalid API key'}), 401

    if not SITE_PASSWORD:
        return
    if request.endpoint in PUBLIC_ROUTES:
        return
    if session.get('site_authenticated'):
        return
    return redirect(url_for('site_login'))

@app.route('/login', methods=['GET', 'POST'])
def site_login():
    """Site-wide password gate."""
    if request.method == 'POST':
        if request.form.get('password') == SITE_PASSWORD:
            session['site_authenticated'] = True
            return redirect(url_for('dashboard'))
        flash('Wrong password.', 'error')
    return render_template('site_login.html')


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


# ==================== API ENDPOINTS ====================

@app.route('/api/clients', methods=['GET'])
def api_clients():
    """List all clients."""
    clients = Client.get_all()
    return jsonify([{'id': c.id, 'name': c.name} for c in clients])


@app.route('/api/clients/<int:client_id>/keywords', methods=['GET', 'POST'])
def api_keywords(client_id):
    """GET: list target keywords. POST: add a target keyword."""
    if request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('keyword'):
            return jsonify({'error': 'keyword is required'}), 400

        target = KeywordTarget(
            client_id=client_id,
            keyword=data['keyword'],
            zone=data.get('zone', 3),
            notes=data.get('notes', '')
        )
        target.save()
        return jsonify({'id': target.id, 'keyword': target.keyword, 'zone': target.zone}), 201

    targets = KeywordTarget.get_by_client(client_id)
    return jsonify([{
        'id': t.id,
        'keyword': t.keyword,
        'zone': t.zone,
        'status': t.status,
        'last_seen_position': t.last_seen_position,
        'last_seen_impressions': t.last_seen_impressions,
        'notes': t.notes
    } for t in targets])


@app.route('/api/clients/<int:client_id>/snapshots', methods=['GET', 'POST'])
def api_snapshots(client_id):
    """GET: snapshot info. POST: take a new snapshot."""
    if request.method == 'POST':
        client = Client.get_by_id(client_id)
        if not client or not client.search_console_site:
            return jsonify({'error': 'No GSC site configured'}), 400

        creds_json = client.google_credentials
        if not creds_json:
            return jsonify({'error': 'No Google credentials'}), 400

        try:
            creds = json.loads(creds_json)
            performance = google_docs_service.get_search_performance(
                creds, client.search_console_site, days=28)
            rows = performance.get('rows', [])
            count = GscSnapshot.take_snapshot(client.id, client.search_console_site, rows)
            return jsonify({'keywords_saved': count, 'date': datetime.now().strftime('%Y-%m-%d')})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({
        'latest_snapshot': GscSnapshot.get_latest_snapshot_date(client_id),
        'total_snapshots': GscSnapshot.get_snapshot_count(client_id)
    })


@app.route('/api/clients/<int:client_id>/performance', methods=['GET'])
def api_performance(client_id):
    """Get current GSC performance data for a client."""
    client = Client.get_by_id(client_id)
    if not client or not client.search_console_site:
        return jsonify({'error': 'No GSC site configured'}), 400

    creds_json = client.google_credentials
    if not creds_json:
        return jsonify({'error': 'No Google credentials'}), 400

    try:
        creds = json.loads(creds_json)
        days = request.args.get('days', 28, type=int)
        performance = google_docs_service.get_search_performance(
            creds, client.search_console_site, days=days)
        opportunities = google_docs_service.get_keyword_opportunities(
            creds, client.search_console_site, days=days)
        return jsonify({
            'performance': performance,
            'opportunities': opportunities
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/clients/<int:client_id>/trajectory/<path:keyword>', methods=['GET'])
def api_trajectory(client_id, keyword):
    """Get position trajectory for a keyword."""
    data = GscSnapshot.get_trajectory(client_id, keyword)
    return jsonify(data)


@app.route('/api/clients/<int:client_id>/ecosystem', methods=['POST'])
def api_ecosystem(client_id):
    """Store weekly ecosystem metrics (Instagram, LinkedIn, Substack)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    # Store in a simple key-value format in the database
    conn = __import__('sqlite3').connect(get_db_path())
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ecosystem_weekly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            week_date TEXT NOT NULL,
            platform TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    ''')

    week_date = data.get('week_date', datetime.now().strftime('%Y-%m-%d'))
    entries = data.get('entries', [])
    count = 0

    for entry in entries:
        cursor.execute('''
            INSERT INTO ecosystem_weekly (client_id, week_date, platform, metric_name, metric_value, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (client_id, week_date, entry.get('platform', ''),
              entry.get('metric', ''), entry.get('value', 0),
              entry.get('notes', '')))
        count += 1

    conn.commit()
    conn.close()
    return jsonify({'entries_saved': count, 'week_date': week_date}), 201


@app.route('/api/clients/<int:client_id>/ecosystem', methods=['GET'])
def api_ecosystem_get(client_id):
    """Get ecosystem metrics for a client."""
    conn = __import__('sqlite3').connect(get_db_path())
    conn.row_factory = __import__('sqlite3').Row
    weeks = request.args.get('weeks', 12, type=int)

    rows = conn.execute('''
        SELECT week_date, platform, metric_name, metric_value, notes
        FROM ecosystem_weekly
        WHERE client_id = ?
        ORDER BY week_date DESC, platform
        LIMIT ?
    ''', (client_id, weeks * 20)).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


# ==================== EXPORT ROUTES ====================

def _build_analytics_export(client):
    tables = []
    creds = get_google_credentials()
    if creds and client.analytics_property_id and google_docs_service:
        try:
            pageviews = google_docs_service.get_analytics_pageviews(creds, client.analytics_property_id)
            if pageviews:
                rows = [
                    [r['page'], r['pageviews'], r['users'], r['avg_time']]
                    for r in pageviews.get('rows', [])
                ]
                tables.append({
                    'name': 'Pageviews',
                    'summary': {
                        'Total Pageviews (28d)': pageviews.get('totals', {}).get('pageviews', 0),
                        'Total Users (28d)': pageviews.get('totals', {}).get('users', 0),
                    },
                    'columns': ['Page', 'Pageviews', 'Users', 'Avg Time (s)'],
                    'rows': rows,
                })
        except Exception as e:
            logger.warning(f"Analytics pageviews export failed: {e}")

        try:
            conversions = google_docs_service.get_analytics_conversions(creds, client.analytics_property_id)
            if conversions:
                rows = [
                    [r.get('page', ''), r.get('event', ''), r.get('count', 0), r.get('value', 0)]
                    for r in conversions.get('rows', [])
                ]
                tables.append({
                    'name': 'Conversions',
                    'summary': {
                        'Total Conversions (28d)': conversions.get('totals', {}).get('conversions', 0),
                        'Total Value': conversions.get('totals', {}).get('value', 0),
                    },
                    'columns': ['Page', 'Event', 'Count', 'Value'],
                    'rows': rows,
                })
        except Exception as e:
            logger.warning(f"Analytics conversions export failed: {e}")

    return f"{client.name} — Analytics (28 days)", tables, 'analytics'


def _build_search_console_export(client):
    tables = []
    creds = get_google_credentials()
    if not (creds and client.search_console_site and google_docs_service):
        return f"{client.name} — Search Console", tables, 'search-console'

    site_url = client.search_console_site

    try:
        performance = google_docs_service.get_search_performance(creds, site_url)
        if performance:
            rows = [
                [r['query'], r['clicks'], r['impressions'], r['ctr'], r['position']]
                for r in performance.get('rows', [])
            ]
            tables.append({
                'name': 'Top Queries',
                'summary': {
                    'Site': site_url,
                    'Total Clicks (28d)': performance.get('totals', {}).get('clicks', 0),
                    'Total Impressions (28d)': performance.get('totals', {}).get('impressions', 0),
                },
                'columns': ['Query', 'Clicks', 'Impressions', 'CTR %', 'Position'],
                'rows': rows,
            })
    except Exception as e:
        logger.warning(f"GSC performance export failed: {e}")

    try:
        pages = google_docs_service.get_page_performance(creds, site_url)
        if pages:
            rows = [
                [r['page'], r['clicks'], r['impressions'], r['ctr'], r['position']]
                for r in pages
            ]
            tables.append({
                'name': 'Top Pages',
                'columns': ['Page', 'Clicks', 'Impressions', 'CTR %', 'Position'],
                'rows': rows,
            })
    except Exception as e:
        logger.warning(f"GSC pages export failed: {e}")

    try:
        opportunities = google_docs_service.get_keyword_opportunities(creds, site_url)
        if opportunities:
            rows = [
                [o['query'], o.get('zone_label', ''), o['impressions'], o['clicks'],
                 o['position'], o['priority']]
                for o in opportunities
            ]
            tables.append({
                'name': 'Keyword Opportunities',
                'columns': ['Query', 'Zone', 'Impressions', 'Clicks', 'Position', 'Priority'],
                'rows': rows,
            })
    except Exception as e:
        logger.warning(f"GSC opportunities export failed: {e}")

    try:
        targets = KeywordTarget.get_by_client(client.id)
        if targets:
            rows = [
                [t.keyword,
                 f"Zone {t.zone}",
                 getattr(t, 'status', '') or '',
                 getattr(t, 'position', '') or '',
                 getattr(t, 'impressions', '') or '',
                 getattr(t, 'notes', '') or '']
                for t in targets
            ]
            tables.append({
                'name': 'Target Keywords',
                'columns': ['Keyword', 'Zone', 'Status', 'Position', 'Impressions', 'Notes'],
                'rows': rows,
            })
    except Exception as e:
        logger.warning(f"Target keywords export failed: {e}")

    return f"{client.name} — Search Console ({site_url})", tables, 'search-console'


def _build_multi_site_export(client):
    tables = []
    creds = get_google_credentials()
    if not (creds and google_docs_service):
        return f"{client.name} — Multi-Site", tables, 'multi-site'

    sites = Site.get_all_by_client_id(client.id)
    if not sites and client.search_console_site:
        sites = [Site(id=0, client_id=client.id,
                      url=client.search_console_site,
                      name=client.search_console_site,
                      gsc_property=client.search_console_site)]

    summary_rows = []
    for site in sites:
        clicks = 0
        impressions = 0
        position = 0
        if site.gsc_property:
            try:
                perf = google_docs_service.get_search_performance(creds, site.gsc_property)
                if perf:
                    clicks = perf.get('totals', {}).get('clicks', 0)
                    impressions = perf.get('totals', {}).get('impressions', 0)
                    positions = [r.get('position', 0) for r in perf.get('rows', []) if r.get('position')]
                    position = round(sum(positions) / len(positions), 1) if positions else 0
            except Exception as e:
                logger.warning(f"Multi-site GSC fetch failed for {site.gsc_property}: {e}")
        summary_rows.append([site.name or site.url, clicks, impressions, position])

    summary_rows.sort(key=lambda r: r[1], reverse=True)
    tables.append({
        'name': 'Site Summary (28d)',
        'columns': ['Site', 'Clicks', 'Impressions', 'Avg Position'],
        'rows': summary_rows,
    })

    return f"{client.name} — Multi-Site Overview", tables, 'multi-site'


def _build_content_strategy_export(client):
    tables = []
    creds = get_google_credentials()
    if creds and client.search_console_site and google_docs_service:
        try:
            opportunities = google_docs_service.get_keyword_opportunities(creds, client.search_console_site)
            if opportunities:
                rows = [
                    [o['query'], o.get('zone_label', ''), o['impressions'], o['clicks'],
                     o['position'], o['priority']]
                    for o in opportunities[:20]
                ]
                tables.append({
                    'name': 'Keyword Opportunities',
                    'columns': ['Query', 'Zone', 'Impressions', 'Clicks', 'Position', 'Priority'],
                    'rows': rows,
                })
        except Exception as e:
            logger.warning(f"Strategy opportunities export failed: {e}")

    existing = Content.get_by_client(client.id, limit=50)
    if existing:
        rows = [
            [c.meta_title or c.h1 or 'Untitled',
             getattr(c, 'primary_keyword', '') or '',
             c.published_url or '',
             c.created_at or '']
            for c in existing
        ]
        tables.append({
            'name': 'Existing Content',
            'columns': ['Title', 'Primary Keyword', 'Published URL', 'Created'],
            'rows': rows,
        })

    return f"{client.name} — Content Strategy", tables, 'content-strategy'


def _build_briefs_export(client):
    briefs = Brief.get_by_client(client.id)
    rows = [
        [b.id, b.title or '', b.content_type or '',
         getattr(b, 'primary_keyword', '') or '', b.created_at or '']
        for b in briefs
    ]
    table = {
        'name': 'Briefs',
        'columns': ['ID', 'Title', 'Type', 'Primary Keyword', 'Created'],
        'rows': rows,
    }
    return f"{client.name} — Briefs", [table], 'briefs'


def _build_workspace_export(client):
    tables = []
    briefs = Brief.get_by_client(client.id)
    contents = Content.get_by_client(client.id, limit=50)

    if contents:
        rows = [
            [c.id,
             c.meta_title or c.h1 or 'Untitled',
             c.published_url or '',
             c.created_at or '']
            for c in contents
        ]
        tables.append({
            'name': 'Recent Content',
            'columns': ['ID', 'Title', 'Published URL', 'Created'],
            'rows': rows,
        })

    if briefs:
        rows = [
            [b.id, b.title or '', b.content_type or '', b.created_at or '']
            for b in briefs
        ]
        tables.append({
            'name': 'Recent Briefs',
            'columns': ['ID', 'Title', 'Type', 'Created'],
            'rows': rows,
        })

    return f"{client.name} — Workspace", tables, 'workspace'


def _build_sites_export(client):
    sites = Site.get_all_by_client_id(client.id)
    rows = [
        [s.id, s.name or '', s.url or '', s.gsc_property or '',
         getattr(s, 'created_at', '') or '']
        for s in sites
    ]
    return (f"{client.name} — Sites",
            [{
                'name': 'Sites',
                'columns': ['ID', 'Name', 'URL', 'GSC Property', 'Created'],
                'rows': rows,
            }],
            'sites')


def _build_ad_spend_export(client):
    tables = []
    entries = AdSpend.get_by_client(client.id)
    monthly_totals = AdSpend.get_monthly_totals(client.id)

    if entries:
        rows = [
            [f"{MONTH_NAMES.get(e.month, e.month)} {e.year}",
             e.platform, e.amount, e.currency, e.notes or '']
            for e in entries
        ]
        tables.append({
            'name': 'Entries',
            'columns': ['Month', 'Platform', 'Amount', 'Currency', 'Notes'],
            'rows': rows,
        })

    if monthly_totals:
        rows = [
            [f"{MONTH_NAMES.get(t['month'], t['month'])} {t['year']}",
             t['total'], t.get('currency', 'EUR')]
            for t in monthly_totals
        ]
        tables.append({
            'name': 'Monthly Totals',
            'columns': ['Month', 'Total', 'Currency'],
            'rows': rows,
        })

    return f"{client.name} — Ad Spend", tables, 'ad-spend'


_EXPORT_BUILDERS = {
    'analytics': _build_analytics_export,
    'search-console': _build_search_console_export,
    'multi-site': _build_multi_site_export,
    'content-strategy': _build_content_strategy_export,
    'briefs': _build_briefs_export,
    'workspace': _build_workspace_export,
    'sites': _build_sites_export,
    'ad-spend': _build_ad_spend_export,
}


def _export_response(fmt, title, tables, filename_base):
    subtitle = f"Exported {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if fmt == 'md':
        body = exporter.to_markdown(title, tables, subtitle=subtitle)
        return Response(body, mimetype='text/markdown; charset=utf-8')
    if fmt == 'xlsx':
        body = exporter.to_xlsx(tables)
        return Response(
            body,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename="{filename_base}.xlsx"'}
        )
    abort(400)


@app.route('/export/<section>/<fmt>')
@require_client
def export_section(section, fmt):
    if fmt not in ('md', 'xlsx'):
        abort(400)
    builder = _EXPORT_BUILDERS.get(section)
    if not builder:
        abort(404)
    client = get_current_client()
    title, tables, filename = builder(client)
    return _export_response(fmt, title, tables, filename)


@app.route('/export/content/<int:content_id>/<fmt>')
@require_client
def export_content_view(content_id, fmt):
    if fmt not in ('md', 'xlsx'):
        abort(400)
    client = get_current_client()
    content = Content.get_by_id(content_id)
    if not content or content.client_id != client.id:
        abort(404)

    derived = DerivedContent.get_by_source(content_id)
    tables = [{
        'name': 'Content',
        'summary': {
            'Title': content.meta_title or content.h1 or 'Untitled',
            'Published URL': content.published_url or '—',
            'Created': content.created_at or '',
        },
        'columns': ['Field', 'Value'],
        'rows': [
            ['Meta Title', content.meta_title or ''],
            ['Meta Description', content.meta_description or ''],
            ['H1', content.h1 or ''],
            ['Body', content.body or ''],
        ],
    }]
    if derived:
        tables.append({
            'name': 'Derived Content',
            'columns': ['Platform', 'Content'],
            'rows': [[d.platform, d.content] for d in derived],
        })
    title = f"{client.name} — {content.meta_title or content.h1 or f'Content {content_id}'}"
    return _export_response(fmt, title, tables, f'content-{content_id}')


# ==================== MAIN ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
