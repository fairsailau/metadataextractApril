import streamlit as st
import logging
import json
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def metadata_config():
    """
    Configure metadata extraction parameters
    """
    st.title("Metadata Configuration")
    
    if not st.session_state.authenticated or not st.session_state.client:
        st.error("Please authenticate with Box first")
        return
    
    if not st.session_state.selected_files:
        st.warning("No files selected. Please select files in the File Browser first.")
        if st.button("Go to File Browser", key="go_to_file_browser_button_config"):
            st.session_state.current_page = "File Browser"
            st.rerun()
        return
    
    # Check if document categorization has been performed
    has_categorization = (
        hasattr(st.session_state, "document_categorization") and 
        st.session_state.document_categorization.get("is_categorized", False)
    )
    
    # Display document categorization results if available
    if has_categorization:
        st.subheader("Document Categorization Results")
        
        # Create a table of document types
        categorization_data = []
        for file in st.session_state.selected_files:
            file_id = file["id"]
            file_name = file["name"]
            
            # Get document type from categorization results
            document_type = "Not categorized"
            if file_id in st.session_state.document_categorization["results"]:
                document_type = st.session_state.document_categorization["results"][file_id]["document_type"]
            
            categorization_data.append({
                "File Name": file_name,
                "Document Type": document_type
            })
        
        # Display table
        st.table(categorization_data)
    else:
        st.info("Document categorization has not been performed. You can categorize documents in the Document Categorization page.")
        if st.button("Go to Document Categorization", key="go_to_doc_cat_button"):
            st.session_state.current_page = "Document Categorization"
            st.rerun()
    
    # Extraction method selection
    st.subheader("Extraction Method")
    
    # Ensure extraction_method is initialized in metadata_config
    if "extraction_method" not in st.session_state.metadata_config:
        st.session_state.metadata_config["extraction_method"] = "freeform"
        
    extraction_method = st.radio(
        "Select extraction method",
        ["Freeform", "Structured"],
        index=0 if st.session_state.metadata_config["extraction_method"] == "freeform" else 1,
        key="extraction_method_radio",
        help="Choose between freeform extraction (free text) or structured extraction (with template)"
    )
    
    # Update extraction method in session state
    st.session_state.metadata_config["extraction_method"] = extraction_method.lower()
    
    # Freeform extraction configuration
    if extraction_method == "Freeform":
        st.subheader("Freeform Extraction Configuration")
        
        # Freeform prompt
        freeform_prompt = st.text_area(
            "Freeform prompt",
            value=st.session_state.metadata_config["freeform_prompt"],
            height=150,
            key="freeform_prompt_textarea",
            help="Prompt for freeform extraction. Be specific about what metadata to extract."
        )
        
        # Update freeform prompt in session state
        st.session_state.metadata_config["freeform_prompt"] = freeform_prompt
        
        # Document type specific prompts
        if has_categorization:
            st.subheader("Document Type Specific Prompts")
            st.info("You can customize the freeform prompt for each document type.")
            
            # Get unique document types
            document_types = set()
            for file_id, result in st.session_state.document_categorization["results"].items():
                document_types.add(result["document_type"])
            
            # Initialize document type prompts if not exists
            if "document_type_prompts" not in st.session_state.metadata_config:
                st.session_state.metadata_config["document_type_prompts"] = {}
            
            # Display prompt for each document type
            for doc_type in document_types:
                # Get current prompt for document type
                current_prompt = st.session_state.metadata_config["document_type_prompts"].get(
                    doc_type, st.session_state.metadata_config["freeform_prompt"]
                )
                
                # Display prompt input
                doc_type_prompt = st.text_area(
                    f"Prompt for {doc_type}",
                    value=current_prompt,
                    height=100,
                    key=f"prompt_{doc_type.replace(' ', '_').lower()}",
                    help=f"Customize the prompt for {doc_type} documents"
                )
                
                # Update prompt in session state
                st.session_state.metadata_config["document_type_prompts"][doc_type] = doc_type_prompt
    
    # Structured extraction configuration
    else:
        st.subheader("Structured Extraction Configuration")
        
        # Check if metadata templates are available
        if not hasattr(st.session_state, "metadata_templates") or not st.session_state.metadata_templates:
            st.warning("No metadata templates available. Please refresh templates in the sidebar.")
            return
        
        # Get available templates
        templates = st.session_state.metadata_templates
        
        # Create template options
        template_options = [("", "None - Use custom fields")]
        for template_id, template in templates.items():
            template_options.append((template_id, template["displayName"]))
        
        # Template selection
        st.write("#### Select Metadata Template")
        
        # Document type template mapping
        if has_categorization:
            st.subheader("Document Type Template Mapping")
            st.info("You can map each document type to a specific metadata template.")
            
            # Get unique document types
            document_types = set()
            for file_id, result in st.session_state.document_categorization["results"].items():
                document_types.add(result["document_type"])
            
            # Initialize document type to template mapping if not exists
            if not hasattr(st.session_state, "document_type_to_template"):
                from modules.metadata_template_retrieval import initialize_template_state
                initialize_template_state()
            
            # Display template selection for each document type
            for doc_type in document_types:
                # Get current template for document type
                current_template_id = st.session_state.document_type_to_template.get(doc_type)
                
                # Find index of current template in options
                selected_index = 0
                for i, (template_id, _) in enumerate(template_options):
                    if template_id == current_template_id:
                        selected_index = i
                        break
                
                # Display template selection
                selected_template = st.selectbox(
                    f"Template for {doc_type}",
                    options=[option[1] for option in template_options],
                    index=selected_index,
                    key=f"template_{doc_type.replace(' ', '_').lower()}",
                    help=f"Select a metadata template for {doc_type} documents"
                )
                
                # Find template ID from selected name
                selected_template_id = ""
                for template_id, template_name in template_options:
                    if template_name == selected_template:
                        selected_template_id = template_id
                        break
                
                # Update template in session state
                st.session_state.document_type_to_template[doc_type] = selected_template_id
        
        # General template selection (for all files)
        selected_template_name = st.selectbox(
            "Select a metadata template",
            options=[option[1] for option in template_options],
            index=0,
            key="template_selectbox",
            help="Select a metadata template to use for structured extraction"
        )
        
        # Find template ID from selected name
        selected_template_id = ""
        for template_id, template_name in template_options:
            if template_name == selected_template_name:
                selected_template_id = template_id
                break
        
        # Update template ID in session state
        st.session_state.metadata_config["template_id"] = selected_template_id
        st.session_state.metadata_config["use_template"] = (selected_template_id != "")
        
        # Display template details if selected
        if selected_template_id:
            template = templates[selected_template_id]
            
            st.write("#### Template Details")
            st.write(f"**Name:** {template['displayName']}")
            st.write(f"**ID:** {template['id']}")
            
            # Display fields
            st.write("**Fields:**")
            for field in template["fields"]:
                st.write(f"- {field['displayName']} ({field['type']})")
        
        # Custom fields if no template selected
        else:
            st.write("#### Custom Fields")
            st.write("Define custom fields for structured extraction")
            
            # Initialize custom fields if not exists
            if "custom_fields" not in st.session_state.metadata_config:
                st.session_state.metadata_config["custom_fields"] = []
            
            # Display existing custom fields
            for i, field in enumerate(st.session_state.metadata_config["custom_fields"]):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    field_name = st.text_input(
                        "Field Name",
                        value=field["name"],
                        key=f"field_name_{i}",
                        help="Name of the custom field"
                    )
                
                with col2:
                    field_type = st.selectbox(
                        "Field Type",
                        options=["string", "number", "date", "enum"],
                        index=["string", "number", "date", "enum"].index(field["type"]),
                        key=f"field_type_{i}",
                        help="Type of the custom field"
                    )
                
                with col3:
                    if st.button("Remove", key=f"remove_field_{i}"):
                        st.session_state.metadata_config["custom_fields"].pop(i)
                        st.rerun()
                
                # Update field in session state
                st.session_state.metadata_config["custom_fields"][i]["name"] = field_name
                st.session_state.metadata_config["custom_fields"][i]["type"] = field_type
            
            # Add new field button
            if st.button("Add Field", key="add_field_button"):
                st.session_state.metadata_config["custom_fields"].append({
                    "name": f"Field {len(st.session_state.metadata_config['custom_fields']) + 1}",
                    "type": "string"
                })
                st.rerun()
    
    # AI model selection
    st.subheader("AI Model Selection")
    
    ai_models = [
        "azure__openai__gpt_4o_mini",
        "azure__openai__gpt_4o_2024_05_13",
        "google__gemini_2_0_flash_001",
        "google__gemini_2_0_flash_lite_preview",
        "google__gemini_1_5_flash_001",
        "google__gemini_1_5_pro_001",
        "aws__claude_3_haiku",
        "aws__claude_3_sonnet",
        "aws__claude_3_5_sonnet",
        "aws__claude_3_7_sonnet",
        "aws__titan_text_lite"
    ]
    
    selected_model = st.selectbox(
        "Select AI Model",
        options=ai_models,
        index=ai_models.index(st.session_state.metadata_config["ai_model"]) if st.session_state.metadata_config["ai_model"] in ai_models else 0,
        key="ai_model_selectbox",
        help="Choose the AI model to use for metadata extraction"
    )
    
    # Update AI model in session state
    st.session_state.metadata_config["ai_model"] = selected_model
    
    # Batch processing configuration
    st.subheader("Batch Processing Configuration")
    
    batch_size = st.slider(
        "Batch Size",
        min_value=1,
        max_value=10,
        value=st.session_state.metadata_config["batch_size"],
        step=1,
        key="batch_size_slider",
        help="Number of files to process in parallel"
    )
    
    # Update batch size in session state
    st.session_state.metadata_config["batch_size"] = batch_size
    
    # Continue button
    st.write("---")
    if st.button("Continue to Process Files", key="continue_to_process_button", use_container_width=True):
        st.session_state.current_page = "Process Files"
        st.rerun()
