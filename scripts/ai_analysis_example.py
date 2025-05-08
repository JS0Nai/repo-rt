#!/usr/bin/env python3
# scripts/ai_analysis_example.py
"""
Example script showing how to send repo-mapper output to an AI model API

SIMULATION ONLY - IMPORTANT NOTICE:
-----------------------------------
This script demonstrates the workflow for sending repo-mapper outputs to an AI model,
but it does NOT actually make API calls to any AI service. The generated repo-rt.md
file will contain only a placeholder message.

To use this with a real AI service:
1. Add your AI provider's API client/SDK import
2. Replace the `send_to_ai_model` function with actual API calls
3. Process the real AI response in the returned string

This template is designed to be customized with your preferred AI provider's integration.
"""

import argparse
import json
import os
import sys
import requests
from pathlib import Path

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print("Loaded API keys from .env file")
except ImportError:
    # dotenv is not installed, continue without it
    pass


def load_repository_data(repo_name, output_dir, target_repo_path):
    """
    Load the repo-mapper outputs for sending to an AI model.
    
    Args:
        repo_name: Name of the repository
        output_dir: Directory containing the repo-mapper outputs
        target_repo_path: Absolute path to the repository being analyzed
    
    Returns:
        dict: Repository data ready for analysis
    """
    data = {
        "repo_name": repo_name,
        "repo_path": target_repo_path,
        "structure": "",
        "scan_report": "",
        "readme_content": "",
        "content": {}
    }
    
    output_path = Path(output_dir)
    
    # Load the structure text file
    structure_path = output_path / f"{repo_name}-structure.txt"
    if structure_path.exists():
        with open(structure_path, 'r') as f:
            data["structure"] = f.read()
    else:
        print(f"Warning: Structure file not found at {structure_path}")
    
    # Load the scan report CSV
    scan_path = output_path / f"{repo_name}-scan_report.csv"
    if scan_path.exists():
        with open(scan_path, 'r') as f:
            data["scan_report"] = f.read()
    else:
        print(f"Warning: Scan report not found at {scan_path}")
    
    # Load the selective map JSON
    map_path = output_path / f"{repo_name}-selective_map.json"
    if map_path.exists():
        with open(map_path, 'r') as f:
            data["content"] = json.load(f)
    else:
        print(f"Warning: Selective map not found at {map_path}")
    
    # Try to load README from target repository
    # This is a fallback in case README isn't in the selective map
    readme_path = Path(target_repo_path) / "README.md"
    if readme_path.exists():
        try:
            with open(readme_path, 'r') as f:
                data["readme_content"] = f.read()
        except Exception as e:
            print(f"Warning: Could not read README.md from target repository: {e}")
    
    return data


def format_llm_prompt(repo_data, template_path=None):
    """
    Format the LLM prompt using the template from LLM_Analysis_Prompt_Template.md
    
    Args:
        repo_data: Dictionary containing repository data
        template_path: Optional path to a custom prompt template
    
    Returns:
        str: The formatted prompt
    """
    # Get the repo-mapper directory
    script_dir = Path(__file__).parent
    repo_mapper_dir = script_dir.parent
    
    # Use default template if none provided
    if template_path is None:
        template_path = repo_mapper_dir / "LLM_Analysis_Prompt_Template.md"
    
    # Check if template exists
    if not template_path.exists():
        print(f"Error: Template file not found at {template_path}")
        print("Please ensure LLM_Analysis_Prompt_Template.md exists in the repo-mapper directory")
        return None
    
    # Load template
    try:
        with open(template_path, 'r') as f:
            template = f.read()
    except Exception as e:
        print(f"Error loading template: {e}")
        return None
    
    # Check if README content exists in selective map
    readme_in_map = False
    repo_key = ""
    
    if repo_data['content']:
        repo_key = list(repo_data['content'].keys())[0]
        if "README.md" in repo_data['content'][repo_key]:
            if "_content" in repo_data['content'][repo_key]["README.md"]:
                readme_in_map = True
    
    # Format README content
    readme_content = ""
    if readme_in_map:
        readme_content = "README.md content is included in the selective map JSON (Artifact 4)."
    elif repo_data["readme_content"]:
        readme_content = repo_data["readme_content"]
    else:
        readme_content = "README.md not found or not readable."
    
    # Add an explicit heading about repository identity
    identity_header = f"""
# CRITICAL: REPOSITORY IDENTITY VERIFICATION
- Repository Name: {repo_data['repo_name']}
- Repository Path: {repo_data['repo_path']}
- You MUST use this exact name "{repo_data['repo_name']}" in your analysis
- DO NOT analyze any other repository (like "intelligent_document_processing" or "idp")
- DO NOT make up repository structure, files, or technologies
- ONLY include information found in the provided artifacts
- Your analysis MUST be based solely on the actual files and content provided
- If you cannot determine something, state this clearly rather than inventing details
"""
    
    # Replace placeholders in template
    formatted_prompt = template
    
    # Add the identity header at the top of the prompt, right after the role and task
    task_end_idx = formatted_prompt.find("**Repository Location:")
    if task_end_idx != -1:
        formatted_prompt = formatted_prompt[:task_end_idx] + identity_header + "\n\n" + formatted_prompt[task_end_idx:]
    else:
        # Fallback - prepend to the beginning if we can't find the marker
        formatted_prompt = identity_header + "\n\n" + formatted_prompt
    
    formatted_prompt = formatted_prompt.replace("[PASTE YOUR REPOSITORY'S ABSOLUTE PATH HERE]", 
                                              repo_data["repo_path"])
    formatted_prompt = formatted_prompt.replace("<PASTE CONTENT OF YOUR PROJECT'S MAIN README.md HERE, OR STATE IF FOUND IN SELECTIVE_MAP>", 
                                              readme_content)
    formatted_prompt = formatted_prompt.replace("<PASTE FULL CONTENT OF {repo_name}-structure.txt HERE>", 
                                              repo_data["structure"])
    formatted_prompt = formatted_prompt.replace("<PASTE FULL CONTENT OF {repo_name}-scan_report.csv HERE>", 
                                              repo_data["scan_report"])
    formatted_prompt = formatted_prompt.replace("<PASTE FULL CONTENT OF {repo_name}-selective_map.json HERE>", 
                                              json.dumps(repo_data["content"], indent=2))
    
    return formatted_prompt


def send_to_ai_model(formatted_prompt, repo_name, repo_path, provider="ollama", custom_model=None):
    """
    Send the repository data to an AI model for analysis.
    
    Args:
        formatted_prompt: The fully formatted prompt for the AI model
        repo_name: Name of the repository
        repo_path: Absolute path to the repository
        provider: LLM provider to use (ollama, openai, anthropic, google)
        custom_model: Override the default model for the selected provider
    
    Returns:
        str: The AI model's response
    """
    # Print a preview of the prompt to avoid flooding the console
    preview_length = 500
    prompt_preview = formatted_prompt[:preview_length] + "..." if len(formatted_prompt) > preview_length else formatted_prompt
    print(f"\nPrompt preview (first {preview_length} characters):")
    print("-" * 40)
    print(prompt_preview)
    print("-" * 40)
    print(f"Total prompt length: {len(formatted_prompt)} characters")
    
    # Common system message for all providers
    system_message = f"You are a code analysis expert. Analyze ONLY the '{repo_name}' repository. You MUST NOT analyze any other repository, make up information, or hallucinate details. The repository data is provided in the user message. The repository is called '{repo_name}' located at '{repo_path}'. Be precise and accurate, ONLY discuss files and structures present in the data provided."
    
    # Environment variables for API keys (can be set in .env file)
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    google_api_key = os.environ.get("GOOGLE_API_KEY", "")
    
    # Select provider
    if provider.lower() == "ollama":
        # Default model selection
        model_name = os.environ.get("OLLAMA_MODEL", "qwen3:32b")
        
        # Check if custom model is specified
        if custom_model:
            model_name = custom_model
            
        print(f"\nUsing Ollama for analysis with model: {model_name}...")
        
        # Send request to local Ollama API
        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": formatted_prompt}
                    ],
                    "stream": False
                }
            )
            
    elif provider.lower() == "openai":
        # Default model selection
        model_name = os.environ.get("OPENAI_MODEL", "gpt-4-turbo")
        
        # Check if custom model is specified
        if custom_model:
            model_name = custom_model
            
        print(f"\nUsing OpenAI for analysis with model: {model_name}...")
        
        if not openai_api_key:
            return "Error: OpenAI API key not found. Set OPENAI_API_KEY environment variable."
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": formatted_prompt}
                    ]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"Error from OpenAI API: {response.status_code} - {response.text}"
        
        except Exception as e:
            error_msg = f"Exception while calling OpenAI API: {str(e)}"
            print(error_msg)
            return error_msg
            
    elif provider.lower() == "anthropic":
        # Default model selection
        model_name = os.environ.get("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        
        # Check if custom model is specified
        if custom_model:
            model_name = custom_model
            
        print(f"\nUsing Anthropic Claude for analysis with model: {model_name}...")
        
        if not anthropic_api_key:
            return "Error: Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable."
        
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": anthropic_api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": model_name,
                    "max_tokens": 4000,
                    "system": system_message,
                    "messages": [
                        {"role": "user", "content": formatted_prompt}
                    ]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["content"][0]["text"]
            else:
                return f"Error from Anthropic API: {response.status_code} - {response.text}"
        
        except Exception as e:
            error_msg = f"Exception while calling Anthropic API: {str(e)}"
            print(error_msg)
            return error_msg
            
    elif provider.lower() == "google":
        # Default model selection
        model_name = os.environ.get("GOOGLE_MODEL", "gemini-pro")
        
        # Check if custom model is specified
        if custom_model:
            model_name = custom_model
            
        print(f"\nUsing Google Gemini for analysis with model: {model_name}...")
        
        if not google_api_key:
            return "Error: Google API key not found. Set GOOGLE_API_KEY environment variable."
        
        try:
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={google_api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {"text": system_message + "\n\n" + formatted_prompt}
                            ]
                        }
                    ]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return f"Error from Google API: {response.status_code} - {response.text}"
        
        except Exception as e:
            error_msg = f"Exception while calling Google API: {str(e)}"
            print(error_msg)
            return error_msg
            
    else:
        return f"Error: Unsupported provider '{provider}'. Choose from: ollama, openai, anthropic, or google"
    
    # For Ollama, we need to process the response
    if provider.lower() == "ollama":
        # Check if request was successful
        if response.status_code == 200:
            # Parse the JSON response
            result = response.json()
            print("Successfully received response from Ollama")
            return result["message"]["content"]
        else:
            error_msg = f"Error from Ollama API: {response.status_code} - {response.text}"
            print(error_msg)
            return error_msg
    except Exception as e:
        error_msg = f"Exception while calling Ollama: {str(e)}"
        print(error_msg)
        return error_msg


def save_analysis(analysis, output_file):
    """
    Save the AI analysis to a file.
    
    Args:
        analysis: The analysis text
        output_file: Path to save the analysis
    """
    with open(output_file, 'w') as f:
        f.write(analysis)
    print(f"Analysis saved to {output_file}")


def main():
    # Get the repo-mapper directory
    script_dir = Path(__file__).parent
    repo_mapper_dir = script_dir.parent
    
    parser = argparse.ArgumentParser(description="Send repo-mapper outputs to an AI model for analysis")
    parser.add_argument("repo_name", help="Name of the repository (used in the output filenames)")
    parser.add_argument("target_repo_path", help="Absolute path to the repository being analyzed")
    parser.add_argument("--output-dir", default=str(repo_mapper_dir / "output"), 
                       help="Directory containing repo-mapper outputs")
    parser.add_argument("--analysis-file", default=str(repo_mapper_dir / "repo-rt.md"), 
                       help="File to save the analysis")
    parser.add_argument("--template-file", help="Optional path to a custom prompt template")
    parser.add_argument("--provider", default="ollama", choices=["ollama", "openai", "anthropic", "google"],
                      help="LLM provider to use for analysis (default: ollama)")
    parser.add_argument("--model", help="Specific model to use with the selected provider (overrides default)")
    
    args = parser.parse_args()
    
    # Load repository data
    try:
        repo_data = load_repository_data(args.repo_name, args.output_dir, args.target_repo_path)
    except Exception as e:
        print(f"Error loading repository data: {e}")
        sys.exit(1)
    
    # Format the prompt
    template_path = Path(args.template_file) if args.template_file else None
    formatted_prompt = format_llm_prompt(repo_data, template_path)
    if not formatted_prompt:
        print("Error: Could not format the LLM prompt")
        sys.exit(1)
    
    # Send to AI model
    try:
        analysis = send_to_ai_model(
            formatted_prompt, 
            repo_data["repo_name"], 
            repo_data["repo_path"], 
            args.provider,
            args.model
        )
    except Exception as e:
        print(f"Error getting AI analysis: {e}")
        sys.exit(1)
    
    # Save the analysis
    try:
        save_analysis(analysis, args.analysis_file)
    except Exception as e:
        print(f"Error saving analysis: {e}")
        sys.exit(1)
    
    print("\nAnalysis process completed!")
    
    # Show provider-specific instructions
    if args.provider == "ollama":
        print("\nUsing Ollama for AI analysis. Make sure you have Ollama running locally at http://localhost:11434")
        print("You can change the Ollama model by editing the 'model' parameter in scripts/ai_analysis_example.py")
    elif args.provider == "openai":
        print("\nUsing OpenAI for AI analysis. Make sure the OPENAI_API_KEY environment variable is set.")
        print("Default model: gpt-4-turbo")
    elif args.provider == "anthropic":
        print("\nUsing Anthropic Claude for AI analysis. Make sure the ANTHROPIC_API_KEY environment variable is set.")
        print("Default model: claude-3-opus-20240229")
    elif args.provider == "google":
        print("\nUsing Google Gemini for AI analysis. Make sure the GOOGLE_API_KEY environment variable is set.")
        print("Default model: gemini-pro")


if __name__ == "__main__":
    main()