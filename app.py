"""
Main application file with optimized components integrated.
This is the entry point for the Box Metadata Extraction application.
"""

import streamlit as st
import os
import logging
from datetime import datetime

# Import optimized modules
from modules.session_state_manager import SessionStateManager as SSM
from modules.integration import get_integration
from modules.authentication import authenticate
from modules.file_browser import display_file_browser
from modules.document_categorization import categorize_document
from modules.metadata_template_retrieval import get_metadata_templates, get_template_fields
from modules.metadata_config import configure_metadata_extraction
from modules.processing import process_files
from modules.results_viewer import display_results
from modules.direct_metadata_application_enhanced_fixed import apply_metadata_to_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main application entry point."""
    # Set page config
    st.set_page_config(
        page_title="Box Metadata Extraction",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    SSM.initialize()
    
    # Get integration instance
    integration = get_integration()
    
    # Display header
    st.title("Box Metadata Extraction")
    
    # Authentication
    client = authenticate_box()
    
    if client:
        # Initialize API client if authenticated
        integration.initialize_api_client(client)
        
        # Store client in session state
        SSM.set('client', client)
        SSM.set('authenticated', True)
        
        # Sidebar navigation
        with st.sidebar:
            st.header("Navigation")
            
            # Add metrics expander
            with st.expander("Performance Metrics", expanded=False):
                if st.button("Refresh Metrics"):
                    st.write("Metrics updated")
                
                metrics = integration.get_metrics()
                
                # API metrics
                st.subheader("API Metrics")
                if 'api' in metrics and metrics['api']:
                    st.write(f"Total requests: {metrics['api'].get('requests', 0)}")
                    st.write(f"Success rate: {metrics['api'].get('success_rate', 0):.1f}%")
                    st.write(f"Avg response time: {metrics['api'].get('avg_time', 0):.3f}s")
                else:
                    st.write("No API metrics available yet")
                
                # Batch processing metrics
                st.subheader("Batch Processing Metrics")
                if 'batch' in metrics:
                    st.write(f"Total batches: {metrics['batch'].get('total_batches', 0)}")
                    st.write(f"Total items: {metrics['batch'].get('total_items', 0)}")
                    st.write(f"Success rate: {metrics['batch'].get('overall_success_rate', 0):.1f}%")
                    st.write(f"Items per second: {metrics['batch'].get('items_per_second', 0):.2f}")
                else:
                    st.write("No batch metrics available yet")
                
                # Circuit breaker status
                st.subheader("Circuit Breaker Status")
                if 'circuit_breakers' in metrics:
                    for name, cb_metrics in metrics['circuit_breakers'].items():
                        st.write(f"{name}: {cb_metrics.get('state', 'unknown')}")
            
            # Navigation options
            page = st.radio(
                "Select Page",
                ["File Browser", "Process Files", "View Results", "Apply Metadata"]
            )
            
            # Background jobs section
            st.header("Background Jobs")
            job_manager = integration.job_manager
            
            # Get active jobs
            jobs = job_manager.get_all_jobs(include_completed=False, limit=5)
            
            if jobs:
                for job in jobs:
                    status_color = {
                        "pending": "blue",
                        "running": "orange",
                        "completed": "green",
                        "failed": "red",
                        "cancelled": "gray"
                    }.get(job['status'], "black")
                    
                    st.write(f"Job: {job['name']}")
                    st.write(f"Status: :{status_color}[{job['status']}]")
                    
                    if job['status'] == "running" and job['progress'] > 0:
                        st.progress(job['progress'])
                        if job['progress_message']:
                            st.write(job['progress_message'])
            else:
                st.write("No active jobs")
            
            # Settings section
            st.header("Settings")
            settings = SSM.get('settings', {})
            
            with st.expander("Processing Settings", expanded=False):
                settings['batch_size'] = st.slider(
                    "Batch Size",
                    min_value=1,
                    max_value=50,
                    value=settings.get('batch_size', 10),
                    help="Number of files to process in each batch"
                )
                
                settings['concurrent_requests'] = st.slider(
                    "Concurrent Requests",
                    min_value=1,
                    max_value=20,
                    value=settings.get('concurrent_requests', 5),
                    help="Maximum number of concurrent API requests"
                )
                
                settings['confidence_threshold'] = st.slider(
                    "Confidence Threshold",
                    min_value=0.0,
                    max_value=1.0,
                    value=settings.get('confidence_threshold', 0.7),
                    step=0.05,
                    help="Minimum confidence level for automatic acceptance"
                )
                
                settings['auto_apply'] = st.checkbox(
                    "Auto-apply Metadata",
                    value=settings.get('auto_apply', False),
                    help="Automatically apply metadata after extraction"
                )
                
                settings['cache_enabled'] = st.checkbox(
                    "Enable Caching",
                    value=settings.get('cache_enabled', True),
                    help="Cache API responses to improve performance"
                )
                
                settings['show_debug'] = st.checkbox(
                    "Show Debug Info",
                    value=settings.get('show_debug', False),
                    help="Display additional debugging information"
                )
            
            # Update settings in session state
            SSM.set('settings', settings)
        
        # Main content based on selected page
        if page == "File Browser":
            display_file_browser()
        
        elif page == "Process Files":
            # Get selected files from session state
            selected_files = SSM.get('selected_files', [])
            
            if not selected_files:
                st.warning("Please select files in the File Browser first")
                if st.button("Go to File Browser"):
                    SSM.set('current_page', 'File Browser')
                    st.experimental_rerun()
            else:
                st.header("Process Files")
                st.write(f"Selected {len(selected_files)} files for processing")
                
                # Configure metadata extraction
                extraction_config = configure_metadata_extraction()
                
                if extraction_config:
                    # Process files with optimized batch processing
                    settings = SSM.get('settings', {})
                    
                    # Use background processing if enabled
                    use_background = st.checkbox(
                        "Process in Background",
                        value=True,
                        help="Run processing in the background to avoid blocking the UI"
                    )
                    
                    if st.button("Start Processing"):
                        if use_background:
                            # Get file IDs
                            file_ids = [file['id'] for file in selected_files]
                            
                            # Start background job
                            job_id = integration.background_batch_extract_metadata(
                                file_ids,
                                prompt=extraction_config.get('prompt'),
                                fields=extraction_config.get('fields'),
                                batch_size=settings.get('batch_size', 10),
                                max_workers=settings.get('concurrent_requests', 5)
                            )
                            
                            # Store job ID
                            SSM.set('active_job_id', job_id)
                            
                            st.success(f"Processing started in background (Job ID: {job_id})")
                            st.info("You can continue using the application while processing runs")
                        else:
                            # Process files synchronously
                            with st.spinner("Processing files..."):
                                results = process_files(
                                    selected_files,
                                    extraction_config,
                                    batch_size=settings.get('batch_size', 10),
                                    concurrent_requests=settings.get('concurrent_requests', 5)
                                )
                                
                                # Store results in session state
                                SSM.set('extraction_results', results)
                                
                                st.success(f"Processed {len(results)} files")
                                
                                # Auto-navigate to results
                                SSM.set('current_page', 'View Results')
                                st.experimental_rerun()
        
        elif page == "View Results":
            # Get results from session state
            results = SSM.get('extraction_results', {})
            
            if not results:
                st.warning("No extraction results available")
                
                # Check for active job
                job_id = SSM.get('active_job_id')
                
                if job_id:
                    job_info = integration.job_manager.get_job(job_id)
                    
                    if job_info and job_info['status'] == 'completed':
                        st.info("Background processing job completed. Loading results...")
                        
                        # Store results in session state
                        SSM.set('extraction_results', job_info['result'])
                        
                        # Clear active job
                        SSM.set('active_job_id', None)
                        
                        # Refresh page
                        st.experimental_rerun()
                    elif job_info and job_info['status'] == 'running':
                        st.info(f"Background processing job is still running ({job_info['progress']*100:.0f}% complete)")
                        st.progress(job_info['progress'])
                        
                        if job_info['progress_message']:
                            st.write(job_info['progress_message'])
                        
                        if st.button("Refresh Status"):
                            st.experimental_rerun()
                    elif job_info and job_info['status'] == 'failed':
                        st.error(f"Background processing job failed: {job_info['error']}")
                        
                        # Clear active job
                        SSM.set('active_job_id', None)
                
                if st.button("Go to Process Files"):
                    SSM.set('current_page', 'Process Files')
                    st.experimental_rerun()
            else:
                # Display results
                display_results(results)
        
        elif page == "Apply Metadata":
            # Get results from session state
            results = SSM.get('extraction_results', {})
            
            if not results:
                st.warning("No extraction results available to apply")
                
                if st.button("Go to Process Files"):
                    SSM.set('current_page', 'Process Files')
                    st.experimental_rerun()
            else:
                # Apply metadata
                apply_metadata_to_files(results)
    else:
        st.warning("Please authenticate with Box to continue")

if __name__ == "__main__":
    main()
