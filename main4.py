import sys
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import time
import random
from datetime import datetime
from typing import Dict, Any, List

# MongoDB imports
from pymongo import MongoClient
from bson.objectid import ObjectId
from pymongo.errors import ConnectionFailure

# Email imports
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Groq for LLM and simulated data generation
from groq import Groq

# Load environment variables from .env file
load_dotenv()

# --- MongoDB Configuration ---
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'supply_chain_db')

client = None
db = None
try:
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    client.admin.command('ping')
    print(f"MongoDB connected successfully to database: {MONGO_DB_NAME}", file=sys.stderr)
except ConnectionFailure as e:
    print(f"Failed to connect to MongoDB: {e}. Please ensure MongoDB is running and MONGO_URI is correct.", file=sys.stderr)
    db = None
except Exception as e:
    print(f"An unexpected error occurred during MongoDB connection: {e}", file=sys.stderr)
    db = None

# --- Email Configuration ---
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
EMAIL_USERNAME = os.environ.get('EMAIL_USERNAME')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
RAW_PRODUCT_STORAGE_EMAIL = os.environ.get('RAW_PRODUCT_STORAGE_EMAIL', 'raw_storage@example.com')
MANUFACTURING_EMAIL = os.environ.get('MANUFACTURING_EMAIL', 'manufacturing@example.com')

# --- App ID for Collection Naming ---
APP_IDENTIFIER = os.environ.get('APP_IDENTIFIER', 'default-app-id')

# --- Initialize Groq Client (Conditional) ---
groq_client = None
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
if GROQ_API_KEY and GROQ_API_KEY.strip():
    try:
        groq_client = Groq(api_key=GROQ_API_KEY.strip())
        print("Groq client initialized.", file=sys.stderr)
    except Exception as e:
        print(f"Failed to initialize Groq client: {e}. Check GROQ_API_KEY.", file=sys.stderr)
        groq_client = None
else:
    print("GROQ_API_KEY not found or is empty. LLM-powered reasoning and simulated data will be skipped.", file=sys.stderr)
    groq_client = None


# --- MongoDB Utility Functions ---
def get_collection_name(base_name: str) -> str:
    """Constructs the MongoDB collection name using the app identifier."""
    return f"{base_name}_{APP_IDENTIFIER}"

def _get_object_id(doc_id: str):
    """Helper to safely convert a string to ObjectId if it's a valid hex string.
    Otherwise, returns the original string.
    """
    if ObjectId.is_valid(doc_id):
        return ObjectId(doc_id)
    return doc_id # Return as string if not a valid ObjectId hex string

def get_mongo_doc(collection_name: str, doc_id: str):
    """Fetches a single document from MongoDB."""
    if db is None: return None
    collection = db[get_collection_name(collection_name)]
    query = {"_id": _get_object_id(doc_id)}
    try:
        return collection.find_one(query)
    except Exception as e:
        print(f"Error fetching doc {doc_id} from {collection_name}: {e}", file=sys.stderr)
        return None

def get_mongo_collection(collection_name: str, query_filters: Dict = None):
    """Fetches documents from a collection, with optional filters."""
    if db is None: return []
    collection = db[get_collection_name(collection_name)]
    filters = {}
    if query_filters:
        filters.update(query_filters)
    return list(collection.find(filters))

def add_mongo_doc(collection_name: str, data: Dict[str, Any]):
    """Adds a new document to a MongoDB collection."""
    if db is None: return None
    collection = db[get_collection_name(collection_name)]
    data["created_at"] = datetime.now()
    data["updated_at"] = datetime.now()
    result = collection.insert_one(data)
    return str(result.inserted_id)

def update_mongo_doc(collection_name: str, doc_id: str, data: Dict[str, Any]):
    """Updates specific fields of a document in a MongoDB collection."""
    if db is None: return None
    collection = db[get_collection_name(collection_name)]
    # Use the helper to determine if it's an ObjectId or a plain string ID
    filter_query = {"_id": _get_object_id(doc_id)}
    data["updated_at"] = datetime.now()
    collection.update_one(filter_query, {"$set": data})
    return doc_id

def delete_mongo_doc(collection_name: str, doc_id: str):
    """Deletes a document from a MongoDB collection."""
    if db is None: return None
    collection = db[get_collection_name(collection_name)]
    filter_query = {"_id": _get_object_id(doc_id)}
    result = collection.delete_one(filter_query)
    return result.deleted_count > 0

def send_email(to_email: str, subject: str, body: str):
    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        print("Email credentials not set. Skipping email sending.", file=sys.stderr)
        return False
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USERNAME
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {to_email}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}", file=sys.stderr)
        return False

# --- Enterprise Supply Chain Agent ---
class EnterpriseSupplyChainAgent:
    def __init__(self, db_instance, groq_client_instance):
        self.db = db_instance
        self.groq_client = groq_client_instance
        self.automation_log = []
        self.locations_map = {}
        self.products_map = {}
        self.inventory_map = {}
        self.store_limits_map = {}
        self.transport_routes = []
        self.latest_weather_data = {}
        self.active_news_events = []

    def _log(self, message: str):
        """Appends a message to the internal automation log."""
        self.automation_log.append(message)
        print(message, file=sys.stderr) # Also print to stderr for immediate console visibility

    def _call_llm_for_generation(self, prompt: str, model: str = "llama3-8b-8192") -> str:
        """Helper to call Groq LLM for generating text."""
        if not self.groq_client:
            return "Groq client not available. Cannot generate data."
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=0.7,
                max_tokens=500,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            self._log(f"Error calling Groq LLM for generation: {e}")
            return f"Error generating data: {e}"

    def _call_llm_for_reasoning(self, prompt: str, model: str = "llama3-8b-8192") -> str:
        """Helper to call Groq LLM for main agent reasoning."""
        if not self.groq_client:
            return "Groq client not available. Cannot perform advanced reasoning."
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=0.5, # Slightly lower temperature for more focused reasoning
                max_tokens=1000,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            self._log(f"Error calling Groq LLM for reasoning: {e}")
            return f"Error performing reasoning: {e}"

    def _gather_data(self):
        """Phase 1: Gathers all necessary data from MongoDB and uses Groq for external data."""
        self._log("Phase 1: Data Gathering Initiated.")

        self.locations_map = {loc['location_id']: loc for loc in get_mongo_collection("Locations")}
        self.products_map = {p['product_id']: p for p in get_mongo_collection("Products")}

        inventory_docs_raw = get_mongo_collection("Inventory")
        self.inventory_map = {}
        for item in inventory_docs_raw:
            composite_key = f"{item['product_id']}_{item['location_id']}"
            self.inventory_map[composite_key] = {
                "doc_id": str(item['_id']),
                "current_stock": item['current_stock']
            }

        store_limits_docs = get_mongo_collection("StoreLimits")
        self.store_limits_map = {f"{item['product_id']}_{item['location_id']}": item for item in store_limits_docs}

        self.transport_routes = get_mongo_collection("TransportationRoutes")

        # --- Use Groq for Weather Data Generation ---
        self._log("  Using Groq to generate weather data...")
        for loc_id, loc_data in self.locations_map.items():
            if 'latitude' in loc_data and 'longitude' in loc_data:
                weather_prompt = (
                    f"Generate a current weather report for {loc_data['location_name']}, {loc_data['city']}, {loc_data['country']}. "
                    "Include temperature in Celsius and a brief condition (e.g., 'Clear', 'Rain', 'Snow', 'Storm', 'Partly Cloudy'). "
                    "Format: Temperature: X.X°C, Conditions: [Condition]"
                )
                weather_report = self._call_llm_for_generation(weather_prompt)

                temperature_celsius = None
                conditions = "Unknown"

                # Simple parsing of Groq's generated weather report
                if "Temperature:" in weather_report and "Conditions:" in weather_report:
                    try:
                        temp_str = weather_report.split("Temperature: ")[1].split("°C")[0].strip()
                        temperature_celsius = float(temp_str)
                        conditions = weather_report.split("Conditions: ")[1].split("\n")[0].strip()
                    except (ValueError, IndexError):
                        self._log(f"    - Failed to parse Groq weather report for {loc_data['location_name']}: {weather_report}")

                if temperature_celsius is not None:
                    weather_doc = {
                        "location_id": loc_id,
                        "timestamp": datetime.now(),
                        "temperature_celsius": temperature_celsius,
                        "conditions": conditions,
                        "raw_data": weather_report
                    }
                    add_mongo_doc("WeatherData", weather_doc)
                    self.latest_weather_data[loc_id] = weather_doc
                    self._log(f"    - Groq Weather for {loc_data['location_name']}: {conditions}, {temperature_celsius}°C")
                else:
                    self._log(f"    - Groq failed to generate valid weather for {loc_data['location_name']}.")
            else:
                self._log(f"    - Skipping weather for {loc_data['location_name']}: Latitude/Longitude not available.")

        # --- Use Groq for News Events Generation ---
        self._log("  Using Groq to generate news events...")
        news_prompt = (
            "Generate 1-2 plausible news events that could impact a supply chain in France today. "
            "Focus on events like strikes, road closures, or significant weather anomalies. "
            "For each event, provide: "
            "Event Title, Event Description (1 sentence), Event Type (strike/road_closure/weather_anomaly), "
            "Affected City (e.g., Paris, Lyon, Rouen, Marseille, or General if widespread), Impact Factor (1.05 for minor, 1.15 for moderate, 1.30 for major). "
            "Format each event as a JSON object within a list. Example: "
            "[{'event_title': '...', 'event_description': '...', 'event_type': '...', 'affected_city': '...', 'impact_factor': X.X}]"
        )
        news_json_str = self._call_llm_for_generation(news_prompt)

        try:
            generated_news_events = json.loads(news_json_str)
            if not isinstance(generated_news_events, list):
                raise ValueError("Groq did not return a list of JSON objects for news events.")

            self.active_news_events = [] # Clear previous active events
            for event_data in generated_news_events:
                # Map affected_city to location_id if possible
                location_id = None
                if 'affected_city' in event_data:
                    for loc_id, loc_info in self.locations_map.items():
                        if loc_info.get('city', '').lower() == event_data['affected_city'].lower():
                            location_id = loc_id
                            break

                news_doc = {
                    "event_title": event_data.get('event_title', 'Generated News Event'),
                    "event_description": event_data.get('event_description', '')[:500] + "...",
                    "event_type": event_data.get('event_type', 'general_impact'),
                    "location_id": location_id,
                    "start_date": datetime.now(),
                    "end_date": None,
                    "impact_factor": event_data.get('impact_factor', 1.1),
                    "api_source": "Groq LLM Generation"
                }
                add_mongo_doc("NewsEvents", news_doc)
                self.active_news_events.append(news_doc)
                self._log(f"    - Groq News: {news_doc['event_title']} (Type: {news_doc['event_type']})")
        except json.JSONDecodeError as e:
            self._log(f"  - Failed to parse Groq-generated news JSON: {e}. Raw response: {news_json_str}")
        except ValueError as e:
            self._log(f"  - Invalid Groq-generated news format: {e}. Raw response: {news_json_str}")
        except Exception as e:
            self._log(f"  - An unexpected error occurred with Groq news generation: {e}")

        if not self.active_news_events:
            self._log("  - No active news events generated by Groq.")

        self._log("Phase 1: Data Gathering Complete.")

    def _analyze_and_plan(self) -> str:
        """Phase 2: Analyzes gathered data and plans actions using Groq LLM for reasoning."""
        self._log("Phase 2: Analysis and Planning Initiated (Agentic Reasoning).")

        # Prepare context for the Groq LLM
        context_prompt = (
            "You are an expert Supply Chain Optimization Agent. Analyze the following supply chain data "
            "and provide a concise, actionable plan for raw material sourcing (Silicon) and "
            "store replenishment (Conductor). "
            "Identify key risks (e.g., low stock, adverse weather, disruptive news events) "
            "and suggest optimal actions to minimize costs and ensure continuity. "
            "Be specific about quantities, locations, and potential impacts. "
            "Conclude with a clear, prioritized list of recommended actions.\n\n"
        )

        context_prompt += "\n--- Current Inventory ---\n"
        for key, inv_data in self.inventory_map.items():
            product_id, loc_id = key.split('_')
            product_name = self.products_map.get(product_id, {}).get('product_name', product_id)
            location_name = self.locations_map.get(loc_id, {}).get('location_name', loc_id)
            context_prompt += f"- {product_name} at {location_name}: {inv_data['current_stock']} units.\n"

        context_prompt += "\n--- Store Limits ---\n"
        for key, limit_data in self.store_limits_map.items():
            product_id, loc_id = key.split('_')
            product_name = self.products_map.get(product_id, {}).get('product_name', product_id)
            location_name = self.locations_map.get(loc_id, {}).get('location_name', loc_id)
            context_prompt += f"- {product_name} at {location_name}: Base Limit {limit_data['base_limit']}, Max Limit {limit_data['max_limit']}.\n"

        context_prompt += "\n--- Latest Weather Data ---\n"
        if self.latest_weather_data:
            for loc_id, weather_data in self.latest_weather_data.items():
                location_name = self.locations_map.get(loc_id, {}).get('location_name', loc_id)
                context_prompt += f"- {location_name}: Temp {weather_data.get('temperature_celsius')}°C, Conditions: {weather_data.get('conditions')}.\n"
        else:
            context_prompt += "- No recent weather data available.\n"

        context_prompt += "\n--- Active News Events ---\n"
        if self.active_news_events:
            for event in self.active_news_events:
                loc_name = self.locations_map.get(event.get('location_id'), {}).get('location_name', 'General')
                context_prompt += f"- Type: {event.get('event_type')}, Title: {event.get('event_title')}, Location: {loc_name}, Impact Factor: {event.get('impact_factor')}.\n"
        else:
            context_prompt += "- No active news events.\n"

        context_prompt += "\n--- Transportation Routes (Cost per kg) ---\n"
        for route in self.transport_routes:
            origin_name = self.locations_map.get(route['origin_location_id'], {}).get('location_name', route['origin_location_id'])
            dest_name = self.locations_map.get(route['destination_location_id'], {}).get('location_name', route['destination_location_id'])
            context_prompt += f"- From {origin_name} to {dest_name}: {route['base_cost_per_kg']} USD/kg.\n"

        context_prompt += "\n--- Suppliers (Raw Material Costs) ---\n"
        raw_material_costs = get_mongo_collection("RawMaterialCosts")
        for cost_info in raw_material_costs:
            product_name = self.products_map.get(cost_info['product_id'], {}).get('product_name', cost_info['product_id'])
            supplier_name = get_mongo_collection("Suppliers", {"supplier_id": cost_info['supplier_id']})
            supplier_name = supplier_name[0]['supplier_name'] if supplier_name else cost_info['supplier_id']
            context_prompt += f"- {product_name} from {supplier_name}: {cost_info['cost_per_unit']} USD/unit.\n"

        self._log("\n--- Agent's Input Context for LLM ---\n" + context_prompt + "\n------------------------------------")

        llm_reasoning = self._call_llm_for_reasoning(context_prompt)
        self._log("\n--- Agent's LLM Reasoning & Plan ---\n" + llm_reasoning + "\n------------------------------------")

        self._log("Phase 2: Analysis and Planning Complete.")
        return llm_reasoning

    def _execute_actions(self, run_id: str):
        """Phase 3: Executes planned actions based on analysis."""
        self._log("Phase 3: Action Execution Initiated.")

        # --- Raw Material Sourcing Logic (for Silicon) ---
        self._log("  Optimizing raw material sourcing (Silicon)...")
        manufacturing_location_id = next((loc['location_id'] for loc in self.locations_map.values() if loc['location_type'] == 'manufacturing'), None)

        if not manufacturing_location_id:
            self._log("  Error: Manufacturing location not found. Cannot source raw materials.")
        else:
            silicon_product_id = next((pid for pid, pdata in self.products_map.items() if pdata.get('product_name') == 'Silicon'), None)
            if silicon_product_id:
                manufacturing_silicon_stock_key = f"{silicon_product_id}_{manufacturing_location_id}"
                current_silicon_inventory_info = self.inventory_map.get(manufacturing_silicon_stock_key, {"current_stock": 0, "doc_id": None})
                current_silicon_stock = current_silicon_inventory_info['current_stock']
                manufacturing_silicon_doc_id = current_silicon_inventory_info['doc_id']

                if current_silicon_stock < 50: # Agent's simple rule: maintain minimum 50kg
                    needed_quantity = 100 - current_silicon_stock # Order up to 100kg
                    self._log(f"    - Manufacturing needs {needed_quantity} kg of Silicon (current: {current_silicon_stock}).")

                    best_supplier = None
                    min_total_cost = float('inf')

                    raw_material_costs = get_mongo_collection("RawMaterialCosts") # Re-fetch for current data
                    silicon_suppliers_costs = [c for c in raw_material_costs if c['product_id'] == silicon_product_id]
                    suppliers = get_mongo_collection("Suppliers") # Re-fetch
                    suppliers_map = {s['supplier_id']: s for s in suppliers}

                    for cost_info in silicon_suppliers_costs:
                        supplier_id = cost_info['supplier_id']
                        supplier_data = suppliers_map.get(supplier_id)
                        if not supplier_data: continue

                        supplier_loc_id = supplier_data.get('supplier_location_id')
                        if not supplier_loc_id: continue

                        route = next((r for r in self.transport_routes if r['origin_location_id'] == supplier_loc_id and r['destination_location_id'] == manufacturing_location_id), None)

                        if route:
                            base_transport_cost_per_kg = route['base_cost_per_kg']
                            adjusted_transport_cost_per_kg = base_transport_cost_per_kg
                            cost_breakdown = {"base_transport_cost_per_kg": base_transport_cost_per_kg}

                            # Apply Groq-generated weather impact
                            if supplier_loc_id in self.latest_weather_data:
                                conditions = self.latest_weather_data[supplier_loc_id].get('conditions', '').lower()
                                if "rain" in conditions or "snow" in conditions or "storm" in conditions:
                                    adjusted_transport_cost_per_kg *= 1.10
                                    cost_breakdown["weather_impact_origin"] = 0.10

                            # Apply Groq-generated news event impact
                            for event in self.active_news_events:
                                if event['location_id'] == supplier_loc_id or event['location_id'] is None:
                                    adjusted_transport_cost_per_kg *= event['impact_factor']
                                    cost_breakdown["news_impact"] = event['impact_factor'] - 1.0

                            total_raw_material_cost = cost_info['cost_per_unit'] * needed_quantity
                            total_transport_cost = adjusted_transport_cost_per_kg * needed_quantity
                            total_cost_for_order = total_raw_material_cost + total_transport_cost

                            if total_cost_for_order < min_total_cost:
                                min_total_cost = total_cost_for_order
                                best_supplier = {
                                    "supplier_id": supplier_id,
                                    "supplier_name": supplier_data['supplier_name'],
                                    "total_cost": total_cost_for_order,
                                    "raw_material_cost": total_raw_material_cost,
                                    "transport_cost": total_transport_cost,
                                    "cost_breakdown": cost_breakdown,
                                    "origin_location_name": self.locations_map[supplier_loc_id]['location_name']
                                }

                    if best_supplier:
                        order_id = f"ORD_RM_{int(time.time())}_{random.randint(100, 999)}"
                        order_data = {
                            "_id": order_id,
                            "product_id": silicon_product_id,
                            "quantity": needed_quantity,
                            "order_type": "raw_material_purchase",
                            "source_location_id": best_supplier['supplier_id'],
                            "destination_location_id": manufacturing_location_id,
                            "order_date": datetime.now(),
                            "delivery_date": None,
                            "status": "pending",
                            "calculated_cost": best_supplier['total_cost'],
                            "cost_breakdown": json.dumps(best_supplier['cost_breakdown']),
                            "optimization_run_id": run_id,
                        }
                        add_mongo_doc("Orders", order_data)
                        self._log(f"    - Raw material order {order_id}: {needed_quantity} kg Silicon from {best_supplier['supplier_name']} to Manufacturing. Total Cost: {best_supplier['total_cost']:.2f}.")

                        email_subject = f"[Supply Chain Alert] Raw Material Order: {needed_quantity} kg {self.products_map[silicon_product_id]['product_name']}"
                        email_body = (
                            f"An automated task has initiated a raw material order:\n\n"
                            f"Product: {self.products_map[silicon_product_id]['product_name']}\n"
                            f"Quantity: {needed_quantity} kg\n"
                            f"Supplier: {best_supplier['supplier_name']} ({best_supplier['origin_location_name']})\n"
                            f"Destination: Manufacturing Plant ({self.locations_map[manufacturing_location_id]['location_name']})\n"
                            f"Calculated Cost: {best_supplier['total_cost']:.2f}\n"
                            f"Urgency: High (stock below limit)\n"
                            f"Weather Impact: {best_supplier['cost_breakdown'].get('weather_impact_origin', 0)*100:.0f}% increase\n"
                            f"News Impact: {best_supplier['cost_breakdown'].get('news_impact', 0)*100:.0f}% increase\n\n"
                            f"Please process this order."
                        )
                        send_email(RAW_PRODUCT_STORAGE_EMAIL, email_subject, email_body)
                        self._log(f"    - Email sent to Raw Product Storage for Silicon order.")
                    else:
                        self._log(f"    - No profitable supplier found for Silicon.")
                else:
                    self._log("  Silicon product not found in Products collection.")

        # --- Store Replenishment Logic (for Conductor) ---
        self._log("  Optimizing store inventory replenishment (Conductor)...")
        manufactured_product_id = next((pid for pid, pdata in self.products_map.items() if pdata.get('product_name') == 'Conductor'), None)

        if not manufactured_product_id:
            self._log("  Error: Manufactured product 'Conductor' not found. Cannot perform store replenishment.")
        else:
            manufacturing_stock_key = f"{manufactured_product_id}_{manufacturing_location_id}"
            current_manufacturing_inventory_info = self.inventory_map.get(manufacturing_stock_key, {"current_stock": 0, "doc_id": None})
            manufacturing_stock = current_manufacturing_inventory_info['current_stock']
            manufacturing_doc_id = current_manufacturing_inventory_info['doc_id']

            self._log(f"  Manufacturing plant ({self.locations_map[manufacturing_location_id]['location_name']}) has {manufacturing_stock} units of Conductor.")

            stores_to_replenish = []
            for store_id, store_data in self.locations_map.items():
                if store_data['location_type'] == 'store':
                    product_store_key = f"{manufactured_product_id}_{store_id}"
                    current_store_inventory_info = self.inventory_map.get(product_store_key, {"current_stock": 0, "doc_id": None})
                    current_stock = current_store_inventory_info['current_stock']
                    store_limit = self.store_limits_map.get(product_store_key)

                    if store_limit and current_stock < store_limit['max_limit']:
                        needed_quantity = store_limit['max_limit'] - current_stock
                        urgency = "High" if current_stock < store_limit['base_limit'] else "Medium"
                        stores_to_replenish.append({
                            "store_id": store_id,
                            "store_name": store_data['location_name'],
                            "needed_quantity": needed_quantity,
                            "current_stock": current_stock,
                            "urgency": urgency
                        })
                        self._log(f"    - Store {store_data['location_name']} needs {needed_quantity} units (current: {current_stock}, base_limit: {store_limit['base_limit']}, max_limit: {store_limit['max_limit']}). Urgency: {urgency}.")

            for store_info in stores_to_replenish:
                destination_id = store_info['store_id']
                quantity_to_order = store_info['needed_quantity']
                urgency = store_info['urgency']

                best_source_id = manufacturing_location_id
                best_route_cost = float('inf')
                best_cost_breakdown = {}

                route_from_manufacturing = next((r for r in self.transport_routes if r['origin_location_id'] == manufacturing_location_id and r['destination_location_id'] == destination_id), None)

                if route_from_manufacturing:
                    base_cost_per_kg = route_from_manufacturing['base_cost_per_kg']
                    adjusted_cost_per_kg = base_cost_per_kg
                    cost_breakdown = {"base_cost_per_kg": base_cost_per_kg}

                    # Apply Groq-generated weather impact
                    if destination_id in self.latest_weather_data:
                        conditions = self.latest_weather_data[destination_id].get('conditions', '').lower()
                        if "rain" in conditions or "snow" in conditions or "storm" in conditions:
                            adjusted_cost_per_kg *= 1.15
                            cost_breakdown["weather_impact"] = 0.15

                    # Apply Groq-generated news event impact
                    for event in self.active_news_events:
                        if event['location_id'] == destination_id or event['location_id'] is None:
                            adjusted_cost_per_kg *= event['impact_factor']
                            cost_breakdown["news_impact"] = event['impact_factor'] - 1.0

                    best_route_cost = adjusted_cost_per_kg * quantity_to_order
                    best_cost_breakdown = cost_breakdown
                    self._log(f"      - Cost from Manufacturing to {store_info['store_name']}: {best_route_cost:.2f}")

                if best_route_cost != float('inf') and manufacturing_stock >= quantity_to_order and manufacturing_doc_id:
                    order_id = f"ORD_ST_{int(time.time())}_{random.randint(100, 999)}"
                    order_data = {
                        "_id": order_id,
                        "product_id": manufactured_product_id,
                        "quantity": quantity_to_order,
                        "order_type": "transfer_to_store",
                        "source_location_id": best_source_id,
                        "destination_location_id": destination_id,
                        "order_date": datetime.now(),
                        "delivery_date": None,
                        "status": "pending",
                        "calculated_cost": best_route_cost,
                        "cost_breakdown": json.dumps(best_cost_breakdown),
                        "optimization_run_id": run_id,
                    }
                    add_mongo_doc("Orders", order_data)

                    new_manufacturing_stock = manufacturing_stock - quantity_to_order
                    update_mongo_doc("Inventory", manufacturing_doc_id, {"current_stock": new_manufacturing_stock})
                    manufacturing_stock = new_manufacturing_stock

                    self._log(f"    - Created order {order_id}: {quantity_to_order} units of Conductor from {self.locations_map[best_source_id]['location_name']} to {store_info['store_name']}. Cost: {best_route_cost:.2f}.")
                    self._log(f"      Manufacturing stock remaining: {manufacturing_stock}")

                    email_subject = f"[Supply Chain Alert] Store Replenishment: {quantity_to_order} units {self.products_map[manufactured_product_id]['product_name']}"
                    email_body = (
                        f"An automated task has initiated a store replenishment order:\n\n"
                        f"Product: {self.products_map[manufactured_product_id]['product_name']}\n"
                        f"Quantity: {quantity_to_order} units\n"
                        f"Source: Manufacturing Plant ({self.locations_map[best_source_id]['location_name']})\n"
                        f"Destination: {store_info['store_name']} ({self.locations_map[destination_id]['location_name']})\n"
                        f"Calculated Transport Cost: {best_route_cost:.2f}\n"
                        f"Urgency: {urgency}\n"
                        f"Weather Impact: {best_cost_breakdown.get('weather_impact', 0)*100:.0f}% increase\n"
                        f"News Impact: {best_cost_breakdown.get('news_impact', 0)*100:.0f}% increase\n\n"
                        f"Please prepare this shipment."
                    )
                    send_email(MANUFACTURING_EMAIL, email_subject, email_body)
                    self._log(f"    - Email sent to Manufacturing for store replenishment.")
                else:
                    self._log(f"    - Cannot fulfill order for {store_info['store_name']} (needed {quantity_to_order}) from Manufacturing (stock: {manufacturing_stock}). Considering other options (not implemented).")

        self._log("Phase 3: Action Execution Complete.")

    def run_automation_cycle(self):
        """Orchestrates the full automation cycle."""
        run_id = f"OPT_{int(time.time())}_{random.randint(100,999)}"
        self.automation_log = [] # Reset log for each run

        optimization_run_data = {
            "_id": run_id,
            "run_timestamp": datetime.now(),
            "status": "pending",
            "triggered_by": "enterprise_agent",
            "summary": "Starting enterprise supply chain automation cycle.",
            "details": {}
        }
        add_mongo_doc("OptimizationRuns", optimization_run_data)

        llm_reasoning_output = "Groq client not available. Skipping LLM reasoning and data generation."
        final_status = "failed"
        final_summary = "Groq client not initialized. Automation skipped."

        if self.groq_client:
            try:
                self._gather_data()
                llm_reasoning_output = self._analyze_and_plan()
                self._execute_actions(run_id)

                final_status = "success"
                final_summary = "Enterprise supply chain automation cycle completed successfully."
            except Exception as e:
                final_status = "failed"
                final_summary = f"An error occurred during automation: {str(e)}"
                self._log(final_summary)

        # Update the OptimizationRun document with final status and full log
        update_mongo_doc("OptimizationRuns", run_id, {
            "status": final_status,
            "summary": final_summary,
            "details": json.dumps({
                "log": self.automation_log,
                "agent_reasoning": llm_reasoning_output # Store LLM output
            })
        })

        return {"status": final_status, "message": final_summary, "log": self.automation_log, "agent_reasoning": llm_reasoning_output}

    def _get_inventory_status_text(self) -> str:
        """Generates a text summary of current inventory."""
        # Ensure data is fresh for chat queries
        self.locations_map = {loc['location_id']: loc for loc in get_mongo_collection("Locations")}
        self.products_map = {p['product_id']: p for p in get_mongo_collection("Products")}
        inventory_docs_raw = get_mongo_collection("Inventory")
        self.inventory_map = {}
        for item in inventory_docs_raw:
            composite_key = f"{item['product_id']}_{item['location_id']}"
            self.inventory_map[composite_key] = {
                "doc_id": str(item['_id']),
                "current_stock": item['current_stock']
            }

        inventory_summary = "Current Inventory:\n"
        if not self.inventory_map:
            return "No inventory data available."

        for key, inv_data in self.inventory_map.items():
            product_id, loc_id = key.split('_')
            product_name = self.products_map.get(product_id, {}).get('product_name', product_id)
            location_name = self.locations_map.get(loc_id, {}).get('location_name', loc_id)
            inventory_summary += f"- {product_name} at {location_name}: {inv_data['current_stock']} units.\n"
        return inventory_summary

    def _get_recent_orders_text(self) -> str:
        """Generates a text summary of recent orders."""
        # Ensure data is fresh for chat queries
        self.locations_map = {loc['location_id']: loc for loc in get_mongo_collection("Locations")}
        self.products_map = {p['product_id']: p for p in get_mongo_collection("Products")}

        orders = get_mongo_collection("Orders")
        orders_summary = "Recent Orders:\n"
        if not orders:
            return "No recent orders found."

        # Sort by order_date descending
        sorted_orders = sorted(orders, key=lambda x: x.get('order_date', datetime.min), reverse=True)[:5] # Get top 5

        for order in sorted_orders:
            product_name = self.products_map.get(order.get('product_id', ''), {}).get('product_name', order.get('product_id', 'Unknown Product'))
            source_name = self.locations_map.get(order.get('source_location_id', ''), {}).get('location_name', order.get('source_location_id', 'Unknown Source'))
            dest_name = self.locations_map.get(order.get('destination_location_id', ''), {}).get('location_name', order.get('destination_location_id', 'Unknown Destination'))

            orders_summary += (
                f"- Order ID: {order.get('_id', 'N/A')}, Product: {product_name}, Quantity: {order.get('quantity', 'N/A')}, "
                f"From: {source_name}, To: {dest_name}, Status: {order.get('status', 'N/A')}, "
                f"Cost: ${order.get('calculated_cost', 0):.2f}\n"
            )
        return orders_summary

    def process_chat_message(self, chat_history: List[Dict[str, str]], user_message: str) -> Dict[str, Any]:
        """
        Processes a user's chat message using Groq to determine intent and generate a response.
        """
        if not self.groq_client:
            return {"response": "Groq client not initialized. Cannot process chat messages.", "triggered_automation": False}

        self._log(f"Processing chat message: '{user_message}'")

        # Prepare messages for LLM to understand intent and generate response
        # The system prompt guides the LLM on its role and capabilities.
        messages_for_llm = [
            {"role": "system", "content": (
                "You are an Enterprise Supply Chain Agent. Your task is to understand user queries "
                "related to supply chain operations. You can answer questions about inventory, "
                "recent orders, and you can trigger the full supply chain automation cycle. "
                "If the user asks to 'run automation' or similar, explicitly state that you are triggering it "
                "by starting your response with the special token 'ACTION:RUN_AUTOMATION'. "
                "If the user asks for inventory status, start your response with 'ACTION:GET_INVENTORY'. "
                "If the user asks for recent orders, start your response with 'ACTION:GET_ORDERS'. "
                "For any other general questions, provide a direct, helpful answer. "
                "Always be concise and professional. After the ACTION token, provide your natural language response."
            )}
        ]

        # Add historical chat for context
        for msg in chat_history:
            messages_for_llm.append({"role": msg['sender'], "content": msg['message']})

        # Add the current user message
        messages_for_llm.append({"role": "user", "content": user_message})

        # Add current supply chain context to the prompt for better understanding
        # This provides RAG-like capabilities by injecting relevant data.
        current_context = (
            f"Current Inventory Status:\n{self._get_inventory_status_text()}\n\n"
            f"Recent Orders Status:\n{self._get_recent_orders_text()}"
        )
        messages_for_llm.append({"role": "system", "content": f"Relevant Supply Chain Data:\n{current_context}"})

        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=messages_for_llm,
                model="llama3-8b-8192",
                temperature=0.6,
                max_tokens=500,
            )
            llm_raw_response = chat_completion.choices[0].message.content
            self._log(f"LLM raw response: {llm_raw_response}")

            triggered_automation = False
            agent_response_content = llm_raw_response

            # --- Intent Recognition and Tool Dispatch ---
            if llm_raw_response.strip().upper().startswith("ACTION:RUN_AUTOMATION"):
                triggered_automation = True
                self._log("Agent intent: TRIGGER_AUTOMATION.")
                agent_response_content = llm_raw_response.replace("ACTION:RUN_AUTOMATION", "").strip()

                automation_result = self.run_automation_cycle()
                agent_response_content += f"\n\n**Automation Result:** {automation_result['message']}\n"
                agent_response_content += "\n".join(automation_result['log'])
                agent_response_content += f"\n\n**Agent's Reasoning for Automation:**\n{automation_result['agent_reasoning']}"
            elif llm_raw_response.strip().upper().startswith("ACTION:GET_INVENTORY"):
                self._log("Agent intent: GET_INVENTORY.")
                agent_response_content = llm_raw_response.replace("ACTION:GET_INVENTORY", "").strip()
                agent_response_content += f"\n\n{self._get_inventory_status_text()}"
            elif llm_raw_response.strip().upper().startswith("ACTION:GET_ORDERS"):
                self._log("Agent intent: GET_ORDERS.")
                agent_response_content = llm_raw_response.replace("ACTION:GET_ORDERS", "").strip()
                agent_response_content += f"\n\n{self._get_recent_orders_text()}"
            else:
                self._log("Agent intent: General query, direct response.")
                # If no specific action token, the LLM's response is taken as-is.
                # The LLM is expected to answer directly based on the context provided.

            return {"response": agent_response_content, "triggered_automation": triggered_automation}

        except Exception as e:
            self._log(f"Error in process_chat_message: {e}")
            return {"response": f"An error occurred while processing your request: {e}", "triggered_automation": False}


# --- Flask Application Setup ---
app = Flask(__name__)
CORS(app)

# --- API Endpoints ---

@app.route('/api/run_automation', methods=['POST'])
def run_automation_endpoint():
    if db is None:
        return jsonify({"error": "MongoDB database is not initialized. Cannot run automation."}), 500

    # Pass the globally initialized groq_client to the agent
    agent = EnterpriseSupplyChainAgent(db, groq_client)
    result = agent.run_automation_cycle()

    if result["status"] == "success":
        return jsonify({"message": result["message"], "log": result["log"], "agent_reasoning": result["agent_reasoning"]}), 200
    else:
        return jsonify({"error": result["message"], "log": result["log"], "agent_reasoning": result["agent_reasoning"]}), 500

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    if db is None:
        return jsonify({"error": "MongoDB database is not initialized. Cannot process chat."}), 500

    data = request.get_json()
    user_message = data.get('message')
    chat_history = data.get('history', []) # Expects a list of {'sender': 'user/agent', 'message': '...'}

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    agent = EnterpriseSupplyChainAgent(db, groq_client)
    response_data = agent.process_chat_message(chat_history, user_message)

    return jsonify(response_data), 200


# --- General CRUD Endpoints (kept for data management) ---

# Products
@app.route('/api/products', methods=['GET'])
def get_products():
    products = get_mongo_collection("Products")
    for p in products:
        if '_id' in p: p['_id'] = str(p['_id'])
    return jsonify(products), 200

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.get_json()
    if not data or 'product_id' not in data or 'product_name' not in data:
        return jsonify({"error": "Missing product_id or product_name"}), 400

    existing_product = db[get_collection_name("Products")].find_one({"product_id": data['product_id']})
    if existing_product:
        return jsonify({"error": f"Product with ID {data['product_id']} already exists."}), 409

    new_id = add_mongo_doc("Products", data)
    if new_id:
        data['_id'] = new_id
        return jsonify({"message": "Product added successfully", "product": data}), 201
    return jsonify({"error": "Failed to add product"}), 500

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    product = db[get_collection_name("Products")].find_one({"product_id": product_id})
    if product:
        if '_id' in product: product['_id'] = str(product['_id'])
        return jsonify(product), 200
    return jsonify({"error": "Product not found"}), 404

@app.route('/api/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided for update"}), 400

    existing_product_doc = db[get_collection_name("Products")].find_one({"product_id": product_id})
    if not existing_product_doc:
        return jsonify({"error": "Product not found"}), 404

    updated = update_mongo_doc("Products", str(existing_product_doc['_id']), data)
    if updated:
        return jsonify({"message": "Product updated successfully", "id": product_id}), 200
    return jsonify({"error": "Failed to update product"}), 500

@app.route('/api/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    existing_product_doc = db[get_collection_name("Products")].find_one({"product_id": product_id})
    if not existing_product_doc:
        return jsonify({"error": "Product not found"}), 404

    deleted = delete_mongo_doc("Products", str(existing_product_doc['_id']))
    if deleted:
        return jsonify({"message": "Product deleted successfully"}), 200
    return jsonify({"error": "Failed to delete product"}), 500


# Locations
@app.route('/api/locations', methods=['GET'])
def get_locations():
    locations = get_mongo_collection("Locations")
    for loc in locations:
        if '_id' in loc: loc['_id'] = str(loc['_id'])
    return jsonify(locations), 200

@app.route('/api/locations', methods=['POST'])
def add_location():
    data = request.get_json()
    if not data or 'location_id' not in data or 'location_name' not in data:
        return jsonify({"error": "Missing location_id or location_name"}), 400

    existing_location = db[get_collection_name("Locations")].find_one({"location_id": data['location_id']})
    if existing_location:
        return jsonify({"error": "Location with ID {data['location_id']} already exists."}), 409

    new_id = add_mongo_doc("Locations", data)
    if new_id:
        data['_id'] = new_id
        return jsonify({"message": "Location added successfully", "location": data}), 201
    return jsonify({"error": "Failed to add location"}), 500

@app.route('/api/locations/<location_id>', methods=['GET'])
def get_location(location_id):
    location = db[get_collection_name("Locations")].find_one({"location_id": location_id})
    if location:
        if '_id' in location: location['_id'] = str(location['_id'])
        return jsonify(location), 200
    return jsonify({"error": "Location not found"}), 404

@app.route('/api/locations/<location_id>', methods=['PUT'])
def update_location(location_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided for update"}), 400

    existing_location_doc = db[get_collection_name("Locations")].find_one({"location_id": location_id})
    if not existing_location_doc:
        return jsonify({"error": "Location not found"}), 404

    updated = update_mongo_doc("Locations", str(existing_location_doc['_id']), data)
    if updated:
        return jsonify({"message": "Location updated successfully", "id": location_id}), 200
    return jsonify({"error": "Failed to update location"}), 500

@app.route('/api/locations/<location_id>', methods=['DELETE'])
def delete_location(location_id):
    existing_location_doc = db[get_collection_name("Locations")].find_one({"location_id": location_id})
    if not existing_location_doc:
        return jsonify({"error": "Location not found"}), 404

    deleted = delete_mongo_doc("Locations", str(existing_location_doc['_id']))
    if deleted:
        return jsonify({"message": "Location deleted successfully"}), 200
    return jsonify({"error": "Failed to delete location"}), 500


# Inventory
@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    inventory = get_mongo_collection("Inventory")
    for item in inventory:
        if '_id' in item: item['_id'] = str(item['_id'])
    return jsonify(inventory), 200

@app.route('/api/inventory', methods=['POST'])
def add_inventory_item():
    data = request.get_json()
    if not data or 'product_id' not in data or 'location_id' not in data or 'current_stock' not in data:
        return jsonify({"error": "Missing product_id, location_id, or current_stock"}), 400

    existing_inventory = db[get_collection_name("Inventory")].find_one({
        "product_id": data['product_id'],
        "location_id": data['location_id']
    })
    if existing_inventory:
        return jsonify({"error": "Inventory record for this product at this location already exists. Use PUT to update."}), 409

    new_id = add_mongo_doc("Inventory", data)
    if new_id:
        data['_id'] = new_id
        return jsonify({"message": "Inventory item added successfully", "inventory_item": data}), 201
    return jsonify({"error": "Failed to add inventory item"}), 500

@app.route('/api/inventory/<product_id>/<location_id>', methods=['GET'])
def get_specific_inventory(product_id, location_id):
    inventory_item = db[get_collection_name("Inventory")].find_one({
        "product_id": product_id,
        "location_id": location_id,
    })
    if inventory_item:
        if '_id' in inventory_item: inventory_item['_id'] = str(inventory_item['_id'])
        return jsonify(inventory_item), 200
    return jsonify({"error": "Inventory item not found"}), 404

@app.route('/api/inventory/<product_id>/<location_id>', methods=['PUT'])
def update_specific_inventory(product_id, location_id):
    data = request.get_json()
    if not data or 'current_stock' not in data:
        return jsonify({"error": "Missing current_stock in update data"}), 400

    existing_inventory_doc = db[get_collection_name("Inventory")].find_one({
        "product_id": product_id,
        "location_id": location_id,
    })
    if not existing_inventory_doc:
        return jsonify({"error": "Inventory item not found"}), 404

    updated = update_mongo_doc("Inventory", str(existing_inventory_doc['_id']), data)
    if updated:
        return jsonify({"message": "Inventory updated successfully"}), 200
    return jsonify({"error": "Failed to update inventory"}), 500

@app.route('/api/inventory/<product_id>/<location_id>', methods=['DELETE'])
def delete_specific_inventory(product_id, location_id):
    existing_inventory_doc = db[get_collection_name("Inventory")].find_one({
        "product_id": product_id,
        "location_id": location_id,
    })
    if not existing_inventory_doc:
        return jsonify({"error": "Inventory item not found"}), 404

    deleted = delete_mongo_doc("Inventory", str(existing_inventory_doc['_id']))
    if deleted:
        return jsonify({"message": "Inventory item deleted successfully"}), 200
    return jsonify({"error": "Failed to delete inventory item"}), 500


# StoreLimits (similar CRUD as Products/Locations)
@app.route('/api/store_limits', methods=['GET'])
def get_store_limits():
    limits = get_mongo_collection("StoreLimits")
    for item in limits:
        if '_id' in item: item['_id'] = str(item['_id'])
    return jsonify(limits), 200

@app.route('/api/store_limits', methods=['POST'])
def add_store_limit():
    data = request.get_json()
    if not data or 'product_id' not in data or 'location_id' not in data:
        return jsonify({"error": "Missing product_id or location_id"}), 400

    existing_limit = db[get_collection_name("StoreLimits")].find_one({
        "product_id": data['product_id'],
        "location_id": data['location_id']
    })
    if existing_limit:
        return jsonify({"error": "Store limit for this product at this location already exists. Use PUT to update."}), 409

    new_id = add_mongo_doc("StoreLimits", data)
    if new_id:
        data['_id'] = new_id
        return jsonify({"message": "Store limit added successfully", "store_limit": data}), 201
    return jsonify({"error": "Failed to add store limit"}), 500

@app.route('/api/store_limits/<product_id>/<location_id>', methods=['GET'])
def get_specific_store_limit(product_id, location_id):
    limit = db[get_collection_name("StoreLimits")].find_one({
        "product_id": product_id,
        "location_id": location_id,
    })
    if limit:
        if '_id' in limit: limit['_id'] = str(limit['_id'])
        return jsonify(limit), 200
    return jsonify({"error": "Store limit not found"}), 404

@app.route('/api/store_limits/<product_id>/<location_id>', methods=['PUT'])
def update_specific_store_limit(product_id, location_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided for update"}), 400

    existing_limit_doc = db[get_collection_name("StoreLimits")].find_one({
        "product_id": product_id,
        "location_id": location_id,
    })
    if not existing_limit_doc:
        return jsonify({"error": "Store limit not found"}), 404

    updated = update_mongo_doc("StoreLimits", str(existing_limit_doc['_id']), data)
    if updated:
        return jsonify({"message": "Store limit updated successfully"}), 200
    return jsonify({"error": "Failed to update store limit"}), 500

@app.route('/api/store_limits/<product_id>/<location_id>', methods=['DELETE'])
def delete_specific_store_limit(product_id, location_id):
    existing_limit_doc = db[get_collection_name("StoreLimits")].find_one({
        "product_id": product_id,
        "location_id": location_id,
    })
    if not existing_limit_doc:
        return jsonify({"error": "Store limit not found"}), 404

    deleted = delete_mongo_doc("StoreLimits", str(existing_limit_doc['_id']))
    if deleted:
        return jsonify({"message": "Store limit deleted successfully"}), 200
    return jsonify({"error": "Failed to delete store limit"}), 500


# Orders (Read-only for simplicity, creation handled by automation)
@app.route('/api/orders', methods=['GET'])
def get_orders():
    orders = get_mongo_collection("Orders")
    for order in orders:
        if '_id' in order: order['_id'] = str(order['_id'])
        if 'order_date' in order and isinstance(order['order_date'], datetime):
            order['order_date'] = order['order_date'].isoformat()
        if 'delivery_date' in order and isinstance(order['delivery_date'], datetime):
            order['delivery_date'] = order['delivery_date'].isoformat()
    return jsonify(orders), 200

# Optimization Runs (Read-only)
@app.route('/api/optimization_runs', methods=['GET'])
def get_optimization_runs():
    runs = get_mongo_collection("OptimizationRuns")
    for run in runs:
        if '_id' in run: run['_id'] = str(run['_id'])
        if 'run_timestamp' in run and isinstance(run['run_timestamp'], datetime):
            run['run_timestamp'] = run['run_timestamp'].isoformat()
    return jsonify(runs), 200

# Suppliers
@app.route('/api/suppliers', methods=['GET'])
def get_suppliers():
    suppliers = get_mongo_collection("Suppliers")
    for s in suppliers:
        if '_id' in s: s['_id'] = str(s['_id'])
    return jsonify(suppliers), 200

@app.route('/api/suppliers', methods=['POST'])
def add_supplier():
    data = request.get_json()
    if not data or 'supplier_id' not in data or 'supplier_name' not in data:
        return jsonify({"error": "Missing supplier_id or supplier_name"}), 400

    existing_supplier = db[get_collection_name("Suppliers")].find_one({"supplier_id": data['supplier_id']})
    if existing_supplier:
        return jsonify({"error": f"Supplier with ID {data['supplier_id']} already exists."}), 409

    new_id = add_mongo_doc("Suppliers", data)
    if new_id:
        data['_id'] = new_id
        return jsonify({"message": "Supplier added successfully", "supplier": data}), 201
    return jsonify({"error": "Failed to add supplier"}), 500

# RawMaterialCosts
@app.route('/api/raw_material_costs', methods=['GET'])
def get_raw_material_costs():
    costs = get_mongo_collection("RawMaterialCosts")
    for c in costs:
        if '_id' in c: c['_id'] = str(c['_id'])
        if 'effective_date' in c and isinstance(c['effective_date'], datetime):
            c['effective_date'] = c['effective_date'].isoformat()
    return jsonify(costs), 200

@app.route('/api/raw_material_costs', methods=['POST'])
def add_raw_material_cost():
    data = request.get_json()
    if not data or 'product_id' not in data or 'supplier_id' not in data or 'cost_per_unit' not in data:
        return jsonify({"error": "Missing required fields for raw material cost"}), 400

    if 'effective_date' in data and isinstance(data['effective_date'], str):
        try:
            data['effective_date'] = datetime.strptime(data['effective_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid effective_date format. Use %Y-%m-%d."}), 400

    new_id = add_mongo_doc("RawMaterialCosts", data)
    if new_id:
        data['_id'] = new_id
        return jsonify({"message": "Raw material cost added successfully", "cost": data}), 201
    return jsonify({"error": "Failed to add raw material cost"}), 500

# TransportationRoutes
@app.route('/api/transportation_routes', methods=['GET'])
def get_transportation_routes():
    routes = get_mongo_collection("TransportationRoutes")
    for r in routes:
        if '_id' in r: r['_id'] = str(r['_id'])
    return jsonify(routes), 200

@app.route('/api/transportation_routes', methods=['POST'])
def add_transportation_route():
    data = request.get_json()
    if not data or 'origin_location_id' not in data or 'destination_location_id' not in data or 'base_cost_per_kg' not in data:
        return jsonify({"error": "Missing required fields for transportation route"}), 400

    existing_route = db[get_collection_name("TransportationRoutes")].find_one({
        "origin_location_id": data['origin_location_id'],
        "destination_location_id": data['destination_location_id']
    })
    if existing_route:
        return jsonify({"error": "Route between these locations already exists. Use PUT to update."}), 409

    new_id = add_mongo_doc("TransportationRoutes", data)
    if new_id:
        data['_id'] = new_id
        return jsonify({"message": "Transportation route added successfully", "route": data}), 201
    return jsonify({"error": "Failed to add transportation route"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
