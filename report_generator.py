import io
import csv
import logging
from typing import List, Dict
from datetime import datetime

# Use try/except for pandas import in case it's not available
try:
    import pandas as pd
except ImportError:
    pd = None

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Generates reports based on URL indexing check results.
    """
    
    def __init__(self):
        pass
    
    def generate_report(self, report, results: List[Dict]) -> Dict:
        """
        Generate a report from check results.
        
        Args:
            report: Report database model
            results: List of dictionaries containing check results
            
        Returns:
            Dictionary with report metrics and visualizations
        """
        # Count indexed and not indexed URLs
        indexed_count = sum(1 for r in results if r['is_indexed'])
        total_count = len(results)
        
        # Calculate percentages
        indexed_percentage = (indexed_count / total_count * 100) if total_count > 0 else 0
        not_indexed_percentage = 100 - indexed_percentage
        
        # Generate data for charts
        chart_data = {
            'labels': ['Indexed', 'Not Indexed'],
            'data': [indexed_percentage, not_indexed_percentage],
            'colors': ['#28a745', '#dc3545']
        }
        
        # Generate domain-level statistics
        domains = {}
        for r in results:
            try:
                # Extract domain from URL safely
                url = r['url']
                if '//' in url:
                    domain = url.split('//', 1)[-1].split('/', 1)[0]
                else:
                    # Handle URLs without protocol
                    domain = url.split('/', 1)[0]
                
                # Skip empty domains
                if not domain:
                    continue
                    
                if domain not in domains:
                    domains[domain] = {'total': 0, 'indexed': 0}
                
                domains[domain]['total'] += 1
                if r['is_indexed']:
                    domains[domain]['indexed'] += 1
            except Exception as e:
                logger.warning(f"Error extracting domain from URL {r.get('url', 'unknown')}: {str(e)}")
                continue
        
        # Calculate domain indexing rates
        domain_stats = []
        for domain, stats in domains.items():
            indexing_rate = (stats['indexed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            domain_stats.append({
                'domain': domain,
                'total': stats['total'],
                'indexed': stats['indexed'],
                'indexing_rate': round(indexing_rate, 2)
            })
        
        # Sort domain stats by indexing rate descending
        domain_stats.sort(key=lambda x: x['indexing_rate'], reverse=True)
        
        return {
            'indexed_count': indexed_count,
            'total_count': total_count,
            'indexed_percentage': round(indexed_percentage, 2),
            'not_indexed_percentage': round(not_indexed_percentage, 2),
            'chart_data': chart_data,
            'domain_stats': domain_stats
        }
    
    def export_csv(self, report, results: List[Dict]) -> str:
        """
        Export check results as CSV.
        
        Args:
            report: Report database model
            results: List of dictionaries containing check results
            
        Returns:
            CSV data as a string
        """
        try:
            # Handle the case of empty results
            if not results:
                # Create an empty DataFrame with the expected columns
                df = pd.DataFrame(columns=['URL', 'Indexed', 'Checked At'])
            else:
                # Create a DataFrame from results
                df = pd.DataFrame(results)
                
                # Format column names and values
                df = df.rename(columns={
                    'url': 'URL',
                    'is_indexed': 'Indexed',
                    'checked_at': 'Checked At'
                })
                
                # Convert boolean to Yes/No
                df['Indexed'] = df['Indexed'].apply(lambda x: 'Yes' if x else 'No')
                
                # Format date
                df['Checked At'] = df['Checked At'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if x else '')
            
            # Add report information as header rows
            report_name = f"Report: {report.name}"
            report_date = f"Generated on: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            report_stats = f"Indexed URLs: {report.indexed_urls} / {report.total_urls} ({report.indexed_percentage:.1f}%)"
            
            # Create CSV buffer
            buffer = io.StringIO()
            
            # Write report header
            buffer.write(f"{report_name}\n")
            buffer.write(f"{report_date}\n")
            buffer.write(f"{report_stats}\n\n")
            
            # Write DataFrame to CSV with error handling for encoding issues
            df.to_csv(buffer, index=False, encoding='utf-8', errors='replace')
            
            # Get CSV as string
            csv_data = buffer.getvalue()
            
            return csv_data
        except Exception as e:
            logger.error(f"Error generating CSV export: {str(e)}")
            # Return a simple error CSV
            return f"Error generating report: {str(e)}"
