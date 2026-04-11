"""
Google Services - OAuth flow, Docs, Search Console, Analytics
Add this file to your services/ folder
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import Config


class GoogleDocsService:
    SCOPES = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/webmasters.readonly',  # Search Console
        'https://www.googleapis.com/auth/analytics.readonly'     # Analytics
    ]
    
    def __init__(self):
        self.client_config = {
            "web": {
                "client_id": Config.GOOGLE_CLIENT_ID,
                "client_secret": Config.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [Config.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
    
    def get_authorization_url(self, state: str = None) -> Tuple[str, str, str]:
        """
        Generate OAuth authorization URL.
        Returns (auth_url, state, code_verifier)
        """
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri=Config.GOOGLE_REDIRECT_URI
        )

        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'
        )

        return auth_url, state, flow.code_verifier
    
    def exchange_code(self, code: str, code_verifier: str = None) -> dict:
        """
        Exchange authorization code for credentials.
        Returns credentials as dict for storage.
        """
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri=Config.GOOGLE_REDIRECT_URI
        )
        flow.code_verifier = code_verifier

        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
    
    def get_credentials(self, creds_dict: dict) -> Credentials:
        """
        Recreate Credentials object from stored dict.
        """
        return Credentials(
            token=creds_dict['token'],
            refresh_token=creds_dict.get('refresh_token'),
            token_uri=creds_dict['token_uri'],
            client_id=creds_dict['client_id'],
            client_secret=creds_dict['client_secret'],
            scopes=creds_dict['scopes']
        )
    
    def create_document(self, creds_dict: dict, title: str, content: str, 
                        folder_id: str = None) -> Tuple[str, str]:
        """
        Create a new Google Doc with content.
        Returns (doc_id, doc_url)
        """
        credentials = self.get_credentials(creds_dict)
        
        # Create empty document
        docs_service = build('docs', 'v1', credentials=credentials)
        
        doc = docs_service.documents().create(body={
            'title': title
        }).execute()
        
        doc_id = doc['documentId']
        
        # Insert content
        requests = [
            {
                'insertText': {
                    'location': {'index': 1},
                    'text': content
                }
            }
        ]
        
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        # Move to folder if specified
        if folder_id:
            drive_service = build('drive', 'v3', credentials=credentials)
            drive_service.files().update(
                fileId=doc_id,
                addParents=folder_id,
                fields='id, parents'
            ).execute()
        
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        
        return doc_id, doc_url
    
    def create_document_formatted(self, creds_dict: dict, title: str, 
                                   meta_title: str, meta_description: str,
                                   body_content: str) -> Tuple[str, str]:
        """
        Create a formatted Google Doc with title, meta, and body.
        Returns (doc_id, doc_url)
        """
        credentials = self.get_credentials(creds_dict)
        docs_service = build('docs', 'v1', credentials=credentials)
        
        # Create empty document
        doc = docs_service.documents().create(body={
            'title': title
        }).execute()
        
        doc_id = doc['documentId']
        
        # Build content with formatting
        full_content = f"{meta_title}\n\nMeta Description:\n{meta_description}\n\n---\n\n{body_content}"
        
        requests = [
            # Insert all content
            {
                'insertText': {
                    'location': {'index': 1},
                    'text': full_content
                }
            },
            # Format title as Heading 1
            {
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': 1,
                        'endIndex': len(meta_title) + 1
                    },
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_1'
                    },
                    'fields': 'namedStyleType'
                }
            }
        ]
        
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        
        return doc_id, doc_url
    
    def get_document_content(self, creds_dict: dict, doc_id: str) -> str:
        """
        Retrieve plain text content from a Google Doc.
        Used to pull back edited content.
        """
        credentials = self.get_credentials(creds_dict)
        docs_service = build('docs', 'v1', credentials=credentials)
        
        doc = docs_service.documents().get(documentId=doc_id).execute()
        
        # Extract text from document
        content = []
        for element in doc.get('body', {}).get('content', []):
            if 'paragraph' in element:
                for text_run in element['paragraph'].get('elements', []):
                    if 'textRun' in text_run:
                        content.append(text_run['textRun'].get('content', ''))
        
        return ''.join(content)
    
    def check_credentials_valid(self, creds_dict: dict) -> bool:
        """
        Check if stored credentials are still valid.
        """
        try:
            credentials = self.get_credentials(creds_dict)
            
            # Try a simple API call
            docs_service = build('docs', 'v1', credentials=credentials)
            docs_service.documents().create(body={'title': '__test__'}).execute()
            
            return True
        except Exception:
            return False

    # ===== SEARCH CONSOLE METHODS =====
    
    def get_search_console_sites(self, creds_dict: dict) -> List[str]:
        """
        Get list of sites the user has access to in Search Console.
        """
        credentials = self.get_credentials(creds_dict)
        service = build('searchconsole', 'v1', credentials=credentials)
        
        sites = service.sites().list().execute()
        return [site['siteUrl'] for site in sites.get('siteEntry', [])]
    
    def get_search_performance(self, creds_dict: dict, site_url: str, 
                                url_filter: str = None,
                                days: int = 28) -> Dict:
        """
        Get search performance data for a site or specific URL.
        
        Returns:
            {
                'rows': [
                    {'query': str, 'clicks': int, 'impressions': int, 'ctr': float, 'position': float}
                ],
                'totals': {'clicks': int, 'impressions': int}
            }
        """
        credentials = self.get_credentials(creds_dict)
        service = build('searchconsole', 'v1', credentials=credentials)
        
        end_date = datetime.now() - timedelta(days=3)  # Data has 3-day delay
        start_date = end_date - timedelta(days=days)
        
        request_body = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d'),
            'dimensions': ['query'],
            'rowLimit': 25
        }
        
        # Filter by specific URL if provided
        if url_filter:
            request_body['dimensionFilterGroups'] = [{
                'filters': [{
                    'dimension': 'page',
                    'operator': 'contains',
                    'expression': url_filter
                }]
            }]
        
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body=request_body
        ).execute()
        
        rows = []
        for row in response.get('rows', []):
            rows.append({
                'query': row['keys'][0],
                'clicks': row['clicks'],
                'impressions': row['impressions'],
                'ctr': round(row['ctr'] * 100, 2),
                'position': round(row['position'], 1)
            })
        
        return {
            'rows': rows,
            'totals': {
                'clicks': sum(r['clicks'] for r in rows),
                'impressions': sum(r['impressions'] for r in rows)
            }
        }
    
    def get_page_performance(self, creds_dict: dict, site_url: str,
                             days: int = 28) -> List[Dict]:
        """
        Get performance data grouped by page.
        """
        credentials = self.get_credentials(creds_dict)
        service = build('searchconsole', 'v1', credentials=credentials)
        
        end_date = datetime.now() - timedelta(days=3)
        start_date = end_date - timedelta(days=days)
        
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'dimensions': ['page'],
                'rowLimit': 50
            }
        ).execute()
        
        pages = []
        for row in response.get('rows', []):
            pages.append({
                'page': row['keys'][0],
                'clicks': row['clicks'],
                'impressions': row['impressions'],
                'ctr': round(row['ctr'] * 100, 2),
                'position': round(row['position'], 1)
            })
        
        return pages

    def get_keyword_opportunities(self, creds_dict: dict, site_url: str,
                                    days: int = 28) -> List[Dict]:
        """
        Get keyword opportunities — queries ranking positions 5-20 with decent impressions.
        These are "low-hanging fruit" that could benefit from new or improved content.
        """
        credentials = self.get_credentials(creds_dict)
        service = build('searchconsole', 'v1', credentials=credentials)

        end_date = datetime.now() - timedelta(days=3)
        start_date = end_date - timedelta(days=days)

        response = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'dimensions': ['query'],
                'rowLimit': 100
            }
        ).execute()

        opportunities = []
        for row in response.get('rows', []):
            position = row['position']
            impressions = row['impressions']
            # Filter: positions 5-20 with at least 10 impressions
            if 5 <= position <= 20 and impressions >= 10:
                # Priority score: high impressions + close to page 1 = highest priority
                # Position factor: position 5 scores 1.0, position 20 scores 0.0
                position_factor = (20 - position) / 15
                # Normalize impressions (log scale to prevent huge values dominating)
                import math
                impression_factor = math.log10(max(impressions, 1))
                priority_score = round(position_factor * 40 + impression_factor * 60, 1)

                # Zone classification
                if position <= 10:
                    zone = 'Zone 2'
                    zone_label = 'Almost there'
                else:
                    zone = 'Zone 3'
                    zone_label = 'Quick win'

                opportunities.append({
                    'query': row['keys'][0],
                    'clicks': row['clicks'],
                    'impressions': impressions,
                    'ctr': round(row['ctr'] * 100, 2),
                    'position': round(position, 1),
                    'priority': priority_score,
                    'zone': zone,
                    'zone_label': zone_label
                })

        # Sort by priority score descending
        opportunities.sort(key=lambda x: x['priority'], reverse=True)
        return opportunities

    # ===== GOOGLE ANALYTICS METHODS =====
    
    def get_analytics_accounts(self, creds_dict: dict) -> List[Dict]:
        """
        Get list of GA4 properties the user has access to.
        """
        credentials = self.get_credentials(creds_dict)
        service = build('analyticsadmin', 'v1beta', credentials=credentials)
        
        accounts = service.accounts().list().execute()
        
        result = []
        for account in accounts.get('accounts', []):
            # Get properties for this account
            properties = service.properties().list(
                filter=f"parent:{account['name']}"
            ).execute()
            
            for prop in properties.get('properties', []):
                result.append({
                    'account_name': account['displayName'],
                    'property_id': prop['name'].split('/')[-1],
                    'property_name': prop['displayName']
                })
        
        return result
    
    def get_analytics_pageviews(self, creds_dict: dict, property_id: str,
                                 url_filter: str = None,
                                 days: int = 28) -> Dict:
        """
        Get pageview data from GA4.
        
        Returns:
            {
                'rows': [
                    {'page': str, 'pageviews': int, 'users': int, 'avg_time': float}
                ],
                'totals': {'pageviews': int, 'users': int}
            }
        """
        credentials = self.get_credentials(creds_dict)
        service = build('analyticsdata', 'v1beta', credentials=credentials)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        request_body = {
            'dateRanges': [{
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d')
            }],
            'dimensions': [{'name': 'pagePath'}],
            'metrics': [
                {'name': 'screenPageViews'},
                {'name': 'totalUsers'},
                {'name': 'averageSessionDuration'}
            ],
            'limit': 50
        }
        
        # Filter by URL if provided
        if url_filter:
            request_body['dimensionFilter'] = {
                'filter': {
                    'fieldName': 'pagePath',
                    'stringFilter': {
                        'matchType': 'CONTAINS',
                        'value': url_filter
                    }
                }
            }
        
        response = service.properties().runReport(
            property=f'properties/{property_id}',
            body=request_body
        ).execute()
        
        rows = []
        for row in response.get('rows', []):
            rows.append({
                'page': row['dimensionValues'][0]['value'],
                'pageviews': int(row['metricValues'][0]['value']),
                'users': int(row['metricValues'][1]['value']),
                'avg_time': round(float(row['metricValues'][2]['value']), 1)
            })
        
        return {
            'rows': rows,
            'totals': {
                'pageviews': sum(r['pageviews'] for r in rows),
                'users': sum(r['users'] for r in rows)
            }
        }

    def get_analytics_conversions(self, creds_dict: dict, property_id: str,
                                   days: int = 28) -> Dict:
        """
        Get conversion events from GA4 grouped by page.
        Returns pages that triggered key events (purchases, signups, etc.)
        """
        credentials = self.get_credentials(creds_dict)
        service = build('analyticsdata', 'v1beta', credentials=credentials)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        try:
            response = service.properties().runReport(
                property=f'properties/{property_id}',
                body={
                    'dateRanges': [{
                        'startDate': start_date.strftime('%Y-%m-%d'),
                        'endDate': end_date.strftime('%Y-%m-%d')
                    }],
                    'dimensions': [
                        {'name': 'pagePath'},
                        {'name': 'eventName'}
                    ],
                    'metrics': [
                        {'name': 'eventCount'},
                        {'name': 'eventValue'}
                    ],
                    'dimensionFilter': {
                        'filter': {
                            'fieldName': 'eventName',
                            'inListFilter': {
                                'values': ['purchase', 'sign_up', 'generate_lead',
                                           'begin_checkout', 'add_to_cart', 'form_submit']
                            }
                        }
                    },
                    'limit': 100
                }
            ).execute()

            rows = []
            for row in response.get('rows', []):
                rows.append({
                    'page': row['dimensionValues'][0]['value'],
                    'event': row['dimensionValues'][1]['value'],
                    'count': int(row['metricValues'][0]['value']),
                    'value': round(float(row['metricValues'][1]['value']), 2)
                })

            total_conversions = sum(r['count'] for r in rows)
            total_value = sum(r['value'] for r in rows)

            return {
                'rows': rows,
                'totals': {
                    'conversions': total_conversions,
                    'value': total_value
                }
            }
        except Exception:
            return {'rows': [], 'totals': {'conversions': 0, 'value': 0}}
