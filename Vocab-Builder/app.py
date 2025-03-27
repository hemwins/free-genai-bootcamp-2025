import gradio as gr
from utils.llm import generate_vocabulary
import json
import requests  # Import the requests library

def generate_vocab(category: str) -> str:
    try:
        result = generate_vocabulary(category)
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"

def post_vocab(category: str, vocabulary: str) -> str:
    try:
        # Call the postVocabulary API endpoint
        api_url = "http://localhost:4999/api/vocabulary"  # Replace with your API URL
        headers = {'Content-Type': 'application/json'}
        data = {'category': category, 'data': json.loads(vocabulary)}
        
        response = requests.post(api_url, headers=headers, data=json.dumps(data, ensure_ascii=False))
        
        if response.status_code == 200:
            return f"Vocabulary posted successfully! {response.text}"
        else:
            return f"Failed to post vocabulary: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

# Custom CSS to match writing-practice
custom_css = """
.container {
    max-width: 800px !important;
    margin: 0 auto !important;
}
.gradio-container {
    font-family: 'Noto Sans JP', sans-serif !important;
}
"""

def create_ui():
    with gr.Blocks(css=custom_css, title="Japanese Vocabulary Generator") as interface:
        gr.Markdown("# Japanese Vocabulary Generator")
        
        with gr.Row():
            category_input = gr.Textbox(
                label="Category",
                placeholder="Enter thematic category (e.g., weather, food, emotions)",
                scale=2
            )
            generate_button = gr.Button("Generate Vocabulary", variant="primary", scale=1)

        vocab_output = gr.TextArea(
            label="Generated Vocabulary",
            lines=10,
            elem_classes=["large-text-output"]
        )

        with gr.Row():
            save_button = gr.Button("Save Vocabulary", variant="secondary", scale=1)
            clear_button = gr.Button("Clear", variant="secondary", scale=1)

        generate_button.click(
            fn=generate_vocab,
            inputs=[category_input],
            outputs=[vocab_output]
        )
        
        save_button.click(
            fn=post_vocab,
            inputs=[category_input, vocab_output],
            outputs=[vocab_output]
        )

        def clear():
            return "", ""

        clear_button.click(
            fn=clear,
            inputs=[],
            outputs=[category_input, vocab_output]
        )

        gr.Examples(
            examples=[
                ["weather"],
                ["food"],
                ["emotions"]
            ],
            inputs=[category_input],
            label="Examples"
        )
    return interface

if __name__ == "__main__":
    ui = create_ui()
    ui.launch(share=True)