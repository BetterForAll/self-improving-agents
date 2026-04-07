import re

def _parse_knowledge_base(kb_string):
    """Parses the knowledge base string into a structured dictionary."""
    parsed_kb = {}
    lines = kb_string.strip().split('\n')
    current_section = None

    # Helper to clean plan names for dictionary keys
    def clean_plan_name(name):
        return name.lower().replace(':', '').strip()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("Product:"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                product_info = parts[1].strip().split(" -- ", 1)
                parsed_kb["product_name"] = product_info[0].strip()
                parsed_kb["product_description"] = product_info[1].strip() if len(product_info) > 1 else ""
            current_section = None
        elif line.startswith("Pricing:"):
            current_section = "pricing"
            parsed_kb[current_section] = {}
        elif line.startswith("Storage Limits:"):
            current_section = "storage_limits"
            parsed_kb[current_section] = {}
        elif line.startswith("Free Trial:"):
            parsed_kb["free_trial"] = line.split(":", 1)[1].strip()
            current_section = None
        elif line.startswith("Supported Platforms:"):
            parsed_kb["supported_platforms"] = line.split(":", 1)[1].strip()
            current_section = None
        elif line.startswith("Key Features:"):
            current_section = "key_features"
            parsed_kb[current_section] = []
        elif line.startswith("- ") and current_section:
            item = line[2:].strip()
            if current_section in ["pricing", "storage_limits"]:
                if ":" in item: # Ensure it's a key-value pair
                    plan_name, value = item.split(":", 1)
                    parsed_kb[current_section][clean_plan_name(plan_name)] = value.strip()
            elif current_section == "key_features":
                parsed_kb[current_section].append(item)
    return parsed_kb


def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    parsed_kb = _parse_knowledge_base(knowledge_base)
    question_lower = question.lower()
    response_parts = []
    info_found = False

    # Identify requested plan using regex for whole words, prioritizing specific plans
    actual_requested_plan = None
    if re.search(r'\benterprise\b', question_lower):
        actual_requested_plan = "enterprise"
    elif re.search(r'\bpersonal\b', question_lower):
        actual_requested_plan = "personal"
    # For "pro", check if it's in context of pricing/storage to distinguish from product name "CloudSync Pro"
    elif re.search(r'\bpro\b', question_lower) and (
        re.search(r'\bpro plan\b', question_lower) or
        any(k in question_lower for k in ["price", "cost", "storage", "capacity", "limit"])
    ):
        actual_requested_plan = "pro"


    # --- General product description ---
    # Trigger if question is about the product itself, or if "CloudSync Pro" is mentioned
    # without specific keywords for pricing/storage/features etc.
    if (any(k in question_lower for k in ["what is cloudsync pro", "tell me about cloudsync pro", "about your service", "product description"]) or
        (re.search(r'\bcloudsync pro\b', question_lower) and
         not any(k in question_lower for k in ["price", "cost", "storage", "feature", "trial", "platform", "plan"]))):
        if parsed_kb.get("product_name") and parsed_kb.get("product_description"):
            response_parts.append(f"{parsed_kb['product_name']} is a {parsed_kb['product_description']}.")
            info_found = True

    # --- Pricing Information ---
    if any(k in question_lower for k in ["price", "cost", "how much", "pricing"]):
        pricing_info = parsed_kb.get("pricing")
        if pricing_info:
            if actual_requested_plan and actual_requested_plan in pricing_info:
                response_parts.append(f"The {actual_requested_plan.capitalize()} plan costs {pricing_info[actual_requested_plan]}.")
                info_found = True
            elif not actual_requested_plan: # Ask about all prices
                all_prices = []
                for plan, price in pricing_info.items():
                    all_prices.append(f"{plan.capitalize()}: {price}")
                response_parts.append(f"Our pricing plans are: {'; '.join(all_prices)}.")
                info_found = True

    # --- Storage Limits ---
    if any(k in question_lower for k in ["storage", "capacity", "gb", "tb", "limit"]):
        storage_info = parsed_kb.get("storage_limits")
        if storage_info:
            if actual_requested_plan and actual_requested_plan in storage_info:
                response_parts.append(f"The {actual_requested_plan.capitalize()} plan includes {storage_info[actual_requested_plan]} of storage.")
                info_found = True
            elif not actual_requested_plan: # Ask about all storage limits
                all_storage = []
                for plan, limit in storage_info.items():
                    all_storage.append(f"{plan.capitalize()}: {limit}")
                response_parts.append(f"Our storage limits are: {'; '.join(all_storage)}.")
                info_found = True

    # --- Free Trial ---
    if any(k in question_lower for k in ["trial", "free"]):
        free_trial_info = parsed_kb.get("free_trial")
        if free_trial_info:
            response_parts.append(f"We offer a {free_trial_info}.")
            info_found = True

    # --- Supported Platforms ---
    if any(k in question_lower for k in ["platform", "device", "support", "os", "compatibility"]):
        platforms_info = parsed_kb.get("supported_platforms")
        if platforms_info:
            response_parts.append(f"CloudSync Pro supports: {platforms_info}.")
            info_found = True

    # --- Key Features ---
    if any(k in question_lower for k in ["feature", "what does it do", "abilities"]):
        features_info = parsed_kb.get("key_features")
        if features_info:
            response_parts.append(f"Key features include: {', '.join(features_info)}.")
            info_found = True

    # --- Construct final answer ---
    if info_found and response_parts:
        final_answer = " ".join(response_parts)
        # Ensure proper punctuation at the end of the sentence before adding the closing phrase
        if not final_answer.strip().endswith(('.', '!', '?')):
             final_answer += "."
        return final_answer + " Is there anything else I can help you with?"
    else:
        return "Thank you for contacting us. I couldn't find a direct answer to your question in our knowledge base. Please visit our website for more information or try rephrasing your question."