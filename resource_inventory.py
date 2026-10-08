import json
import os
import tempfile
from copy import deepcopy


# ============================================================
# CONFIGURATION
# ============================================================

DATA_FILE = "inventory_data.json"


# ============================================================
# DEFAULT DATA
# ============================================================

DEFAULT_RESOURCES = [
    {
        "id": "R001",
        "name": "Laptop",
        "category": "Electronics",
        "total": 10,
        "available": 10,
    },
    {
        "id": "R002",
        "name": "Keyboard",
        "category": "Accessories",
        "total": 5,
        "available": 5,
    },
    {
        "id": "R003",
        "name": "Headset",
        "category": "Accessories",
        "total": 3,
        "available": 3,
    },
]


DEFAULT_FELLOWS = {
    "F001": "Ada",
    "F002": "John",
    "F003": "Grace",
}


# Live application state.
resources = deepcopy(DEFAULT_RESOURCES)
fellows = deepcopy(DEFAULT_FELLOWS)
borrow_records = []


# ============================================================
# JSON PERSISTENCE
# ============================================================

def validate_data(data):
    """
    Validate the complete structure of saved inventory data.

    Returns:
        (True, "Valid data.") when valid.
        (False, "Reason...") when invalid.
    """

    if not isinstance(data, dict):
        return False, "Saved data must be a JSON object."

    required_keys = {"resources", "fellows", "borrow_records"}

    if set(data.keys()) != required_keys:
        return False, "Saved data must contain resources, fellows, and borrow_records."

    saved_resources = data["resources"]
    saved_fellows = data["fellows"]
    saved_records = data["borrow_records"]

    if not isinstance(saved_resources, list):
        return False, "resources must be a list."

    if not isinstance(saved_fellows, dict):
        return False, "fellows must be an object."

    if not isinstance(saved_records, list):
        return False, "borrow_records must be a list."

    # --------------------------------------------------------
    # Validate fellows
    # --------------------------------------------------------

    for fellow_id, fellow_name in saved_fellows.items():
        if not isinstance(fellow_id, str) or not fellow_id.strip():
            return False, "Every fellow ID must be a non-empty string."

        if not isinstance(fellow_name, str) or not fellow_name.strip():
            return False, f"Fellow '{fellow_id}' has an invalid name."

    # --------------------------------------------------------
    # Validate resources
    # --------------------------------------------------------

    resource_ids = set()

    for resource in saved_resources:
        if not isinstance(resource, dict):
            return False, "Every resource must be an object."

        required_resource_keys = {
            "id",
            "name",
            "category",
            "total",
            "available",
        }

        if set(resource.keys()) != required_resource_keys:
            return False, (
                "Every resource must contain id, name, category, "
                "total, and available."
            )

        resource_id = resource["id"]
        name = resource["name"]
        category = resource["category"]
        total = resource["total"]
        available = resource["available"]

        if not isinstance(resource_id, str) or not resource_id.strip():
            return False, "Every resource ID must be a non-empty string."

        if resource_id in resource_ids:
            return False, f"Duplicate resource ID found: {resource_id}"

        resource_ids.add(resource_id)

        if not isinstance(name, str) or not name.strip():
            return False, f"Resource '{resource_id}' has an invalid name."

        if not isinstance(category, str) or not category.strip():
            return False, f"Resource '{resource_id}' has an invalid category."

        if isinstance(total, bool) or not isinstance(total, int):
            return False, f"Resource '{resource_id}' total must be an integer."

        if total <= 0:
            return False, f"Resource '{resource_id}' total must be greater than zero."

        if isinstance(available, bool) or not isinstance(available, int):
            return False, (
                f"Resource '{resource_id}' available quantity "
                "must be an integer."
            )

        if available < 0 or available > total:
            return False, (
                f"Resource '{resource_id}' has invalid available quantity."
            )

    # --------------------------------------------------------
    # Validate borrow records
    # --------------------------------------------------------

    active_loans = set()
    borrowed_totals = {resource_id: 0 for resource_id in resource_ids}

    for record in saved_records:
        if not isinstance(record, dict):
            return False, "Every borrow record must be an object."

        required_record_keys = {
            "fellow_id",
            "resource_id",
            "quantity",
        }

        if set(record.keys()) != required_record_keys:
            return False, (
                "Every borrow record must contain fellow_id, "
                "resource_id, and quantity."
            )

        fellow_id = record["fellow_id"]
        resource_id = record["resource_id"]
        quantity = record["quantity"]

        if fellow_id not in saved_fellows:
            return False, (
                f"Borrow record references unknown fellow: {fellow_id}"
            )

        if resource_id not in resource_ids:
            return False, (
                f"Borrow record references unknown resource: {resource_id}"
            )

        if isinstance(quantity, bool) or not isinstance(quantity, int):
            return False, "Borrow quantity must be an integer."

        if quantity <= 0:
            return False, "Borrow quantity must be greater than zero."

        loan_key = (fellow_id, resource_id)

        if loan_key in active_loans:
            return False, (
                f"Duplicate active loan found for {fellow_id} "
                f"and {resource_id}."
            )

        active_loans.add(loan_key)
        borrowed_totals[resource_id] += quantity

    # --------------------------------------------------------
    # Verify inventory calculations
    # --------------------------------------------------------

    for resource in saved_resources:
        resource_id = resource["id"]
        expected_available = (
            resource["total"] - borrowed_totals[resource_id]
        )

        if resource["available"] != expected_available:
            return False, (
                f"Inconsistent inventory for {resource_id}: "
                f"expected {expected_available} available, "
                f"found {resource['available']}."
            )

    return True, "Valid data."


def save_data(file_path=DATA_FILE):
    """
    Save the current application state to JSON.

    A temporary file and os.replace() are used so that the existing
    file is not partially overwritten if something goes wrong.
    """

    data = {
        "resources": resources,
        "fellows": fellows,
        "borrow_records": borrow_records,
    }

    valid, message = validate_data(data)

    if not valid:
        return False, f"Cannot save invalid data: {message}"

    directory = os.path.dirname(os.path.abspath(file_path))

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            delete=False,
        ) as temporary_file:

            json.dump(
                data,
                temporary_file,
                indent=4,
                ensure_ascii=False,
            )

            temporary_file.write("\n")
            temporary_path = temporary_file.name

        os.replace(temporary_path, file_path)

        return True, f"Inventory data saved to '{file_path}'."

    except (OSError, TypeError, ValueError) as error:
        try:
            if "temporary_path" in locals() and os.path.exists(temporary_path):
                os.remove(temporary_path)
        except OSError:
            pass

        return False, f"Could not save inventory data: {error}"


def load_data(file_path=DATA_FILE):
    """
    Load inventory state from JSON.

    The live application state is changed only after the entire file
    has been successfully read and validated.
    """

    global resources
    global fellows
    global borrow_records

    if not os.path.exists(file_path):
        return False, "No saved inventory file found. Starting with the default inventory."

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

    except json.JSONDecodeError:
        return False, "Saved inventory file contains invalid JSON."

    except OSError as error:
        return False, f"Could not read inventory data: {error}"

    valid, message = validate_data(data)

    if not valid:
        return False, f"Saved inventory data is invalid: {message}"

    # Only update the live state after successful validation.
    resources = deepcopy(data["resources"])
    fellows = deepcopy(data["fellows"])
    borrow_records = deepcopy(data["borrow_records"])

    return True, "Inventory data loaded successfully."


def initialize_data():
    """
    Load saved data if available.

    If no saved data exists, use the default inventory.
    """

    global resources
    global fellows
    global borrow_records

    resources = deepcopy(DEFAULT_RESOURCES)
    fellows = deepcopy(DEFAULT_FELLOWS)
    borrow_records = []

    loaded, message = load_data()

    print()

    if loaded:
        print(f"Notice: {message}")
    else:
        print(f"Notice: {message}")


# ============================================================
# LOOKUP FUNCTIONS
# ============================================================

def find_resource(resource_id):
    """Return a resource by ID, or None if not found."""

    resource_id = resource_id.strip().upper()

    for resource in resources:
        if resource["id"].upper() == resource_id:
            return resource

    return None


def find_fellow(fellow_id):
    """Return a fellow name by ID, or None if not found."""

    fellow_id = fellow_id.strip().upper()

    for current_id, name in fellows.items():
        if current_id.upper() == fellow_id:
            return name

    return None


def find_fellow_id(fellow_name):
    """Return a fellow ID by name, or None if not found."""

    fellow_name = fellow_name.strip().lower()

    for fellow_id, name in fellows.items():
        if name.lower() == fellow_name:
            return fellow_id

    return None


# ============================================================
# DISPLAY FUNCTIONS
# ============================================================

def display_resource(resource):
    """Display one resource."""

    print(
        f"{resource['id']} | "
        f"{resource['name']} | "
        f"{resource['category']} | "
        f"Total: {resource['total']} | "
        f"Available: {resource['available']}"
    )


def list_resources():
    """Display all resources."""

    print()
    print("--- Resource Inventory ---")

    if not resources:
        print("No resources found.")
        return

    for resource in resources:
        display_resource(resource)


# ============================================================
# RESOURCE MANAGEMENT
# ============================================================

def add_resource():
    """Add a new resource after validating user input."""

    print()
    print("--- Add Resource ---")

    resource_id = input("Enter resource ID: ").strip().upper()

    if not resource_id:
        print("Error: Resource ID cannot be empty.")
        return

    if find_resource(resource_id) is not None:
        print(f"Error: Resource ID '{resource_id}' already exists.")
        return

    name = input("Enter resource name: ").strip()

    if not name:
        print("Error: Resource name cannot be empty.")
        return

    category = input("Enter resource category: ").strip()

    if not category:
        print("Error: Resource category cannot be empty.")
        return

    total_input = input("Enter total units: ").strip()

    try:
        total = int(total_input)
    except ValueError:
        print("Error: Total units must be a whole number.")
        return

    if total <= 0:
        print("Error: Total units must be greater than zero.")
        return

    resource = {
        "id": resource_id,
        "name": name,
        "category": category,
        "total": total,
        "available": total,
    }

    resources.append(resource)

    saved, message = save_data()

    print(f"Resource '{name}' added successfully.")

    if not saved:
        print(f"Warning: Resource was added, but JSON save failed: {message}")


# ============================================================
# BORROWING
# ============================================================

def find_loan(fellow_id, resource_id):
    """Find an active borrowing record."""

    fellow_id = fellow_id.strip().upper()
    resource_id = resource_id.strip().upper()

    for record in borrow_records:
        if (
            record["fellow_id"].upper() == fellow_id
            and record["resource_id"].upper() == resource_id
        ):
            return record

    return None


def borrow_item(fellow_id, resource_id, quantity):
    """
    Borrow a resource.

    Returns:
        (True, success_message)
        (False, error_message)
    """

    fellow_id = fellow_id.strip().upper()
    resource_id = resource_id.strip().upper()

    if fellow_id not in fellows:
        return False, f"Fellow ID '{fellow_id}' was not found."

    resource = find_resource(resource_id)

    if resource is None:
        return False, f"Resource ID '{resource_id}' was not found."

    if isinstance(quantity, bool) or not isinstance(quantity, int):
        return False, "Quantity must be a whole number."

    if quantity <= 0:
        return False, "Quantity must be greater than zero."

    if quantity > resource["available"]:
        return (
            False,
            f"Only {resource['available']} {resource['name']}(s) are available.",
        )

    # --------------------------------------------------------
    # Only modify state after ALL validation succeeds.
    # --------------------------------------------------------

    resource["available"] -= quantity

    existing_loan = find_loan(fellow_id, resource_id)

    if existing_loan is not None:
        existing_loan["quantity"] += quantity
    else:
        borrow_records.append(
            {
                "fellow_id": fellow_id,
                "resource_id": resource_id,
                "quantity": quantity,
            }
        )

    return (
        True,
        f"Success: {fellows[fellow_id]} borrowed "
        f"{quantity} unit(s) of {resource['name']}.",
    )


def borrow_resource():
    """Collect borrowing information from the user."""

    print()
    print("--- Borrow Resource ---")

    fellow_id = input("Enter fellow ID: ").strip().upper()
    resource_id = input("Enter resource ID: ").strip().upper()
    quantity_input = input("Enter quantity: ").strip()

    try:
        quantity = int(quantity_input)
    except ValueError:
        print("Error: Quantity must be a whole number.")
        return

    success, message = borrow_item(
        fellow_id,
        resource_id,
        quantity,
    )

    print(message)

    if success:
        saved, save_message = save_data()

        if not saved:
            print(
                "Warning: Borrowing succeeded in memory, "
                f"but JSON save failed: {save_message}"
            )


# ============================================================
# RETURNS
# ============================================================

def return_item(fellow_id, resource_id, quantity):
    """
    Return a borrowed resource.

    Returns:
        (True, success_message)
        (False, error_message)
    """

    fellow_id = fellow_id.strip().upper()
    resource_id = resource_id.strip().upper()

    if fellow_id not in fellows:
        return False, f"Fellow ID '{fellow_id}' was not found."

    resource = find_resource(resource_id)

    if resource is None:
        return False, f"Resource ID '{resource_id}' was not found."

    if isinstance(quantity, bool) or not isinstance(quantity, int):
        return False, "Quantity must be a whole number."

    if quantity <= 0:
        return False, "Quantity must be greater than zero."

    loan = find_loan(fellow_id, resource_id)

    if loan is None:
        return (
            False,
            f"{fellows[fellow_id]} does not currently have "
            f"{resource['name']} on loan.",
        )

    if quantity > loan["quantity"]:
        return (
            False,
            f"{fellows[fellow_id]} only has "
            f"{loan['quantity']} unit(s) of "
            f"{resource['name']} on loan.",
        )

    # --------------------------------------------------------
    # Only modify state after ALL validation succeeds.
    # --------------------------------------------------------

    resource["available"] += quantity
    loan["quantity"] -= quantity

    if loan["quantity"] == 0:
        borrow_records.remove(loan)

    return (
        True,
        f"Success: {fellows[fellow_id]} returned "
        f"{quantity} unit(s) of {resource['name']}.",
    )


def return_resource():
    """Collect return information from the user."""

    print()
    print("--- Return Resource ---")

    fellow_id = input("Enter fellow ID: ").strip().upper()
    resource_id = input("Enter resource ID: ").strip().upper()
    quantity_input = input("Enter quantity: ").strip()

    try:
        quantity = int(quantity_input)
    except ValueError:
        print("Error: Quantity must be a whole number.")
        return

    success, message = return_item(
        fellow_id,
        resource_id,
        quantity,
    )

    print(message)

    if success:
        saved, save_message = save_data()

        if not saved:
            print(
                "Warning: Return succeeded in memory, "
                f"but JSON save failed: {save_message}"
            )


# ============================================================
# SEARCH AND FILTER
# ============================================================

def search_resources(search_term):
    """Search resources by name, case-insensitively."""

    search_term = search_term.strip().lower()

    if not search_term:
        return []

    return [
        resource
        for resource in resources
        if search_term in resource["name"].lower()
    ]


def filter_by_category(category):
    """Return resources matching a category case-insensitively."""

    category = category.strip().lower()

    return [
        resource
        for resource in resources
        if resource["category"].lower() == category
    ]


def search_resources_menu():
    """Handle resource searching from the menu."""

    print()
    print("--- Search Resources ---")

    search_term = input("Enter resource name to search: ").strip()

    results = search_resources(search_term)

    if not results:
        print("No matching resources found.")
        return

    print()
    print("Matching resources:")

    for resource in results:
        display_resource(resource)


def filter_category_menu():
    """Handle category filtering from the menu."""

    print()
    print("--- Filter by Category ---")

    category = input("Enter category: ").strip()

    results = filter_by_category(category)

    if not results:
        print("No resources found in that category.")
        return

    print()
    print("Matching resources:")

    for resource in results:
        display_resource(resource)


# ============================================================
# REPORTING
# ============================================================

def calculate_borrowed_by_resource():
    """Calculate the number of borrowed units for each resource."""

    borrowed = {
        resource["id"]: resource["total"] - resource["available"]
        for resource in resources
    }

    return borrowed


def generate_report():
    """Generate the required inventory report."""

    total_units = sum(resource["total"] for resource in resources)
    available_units = sum(resource["available"] for resource in resources)
    borrowed_units = total_units - available_units

    low_stock = [
        resource
        for resource in resources
        if resource["available"] < 3
    ]

    borrowed_by_resource = calculate_borrowed_by_resource()

    if borrowed_by_resource:
        highest_borrowed = max(borrowed_by_resource.values())
        most_borrowed = [
            resource
            for resource in resources
            if borrowed_by_resource[resource["id"]] == highest_borrowed
            and highest_borrowed > 0
        ]
    else:
        highest_borrowed = 0
        most_borrowed = []

    print()
    print("--- Inventory Report ---")
    print(f"Total units: {total_units}")
    print(f"Available units: {available_units}")
    print(f"Units currently borrowed: {borrowed_units}")

    print()
    print("Low stock resources:")

    if low_stock:
        for resource in low_stock:
            print(
                f"{resource['name']} "
                f"({resource['available']} available)"
            )
    else:
        print("None")

    print()
    print("Most borrowed resource:")

    if most_borrowed:
        for resource in most_borrowed:
            print(
                f"{resource['name']} "
                f"({borrowed_by_resource[resource['id']]})"
            )
    else:
        print("None")


# ============================================================
# REQUIRED DEMONSTRATION
# ============================================================

def run_required_demonstration():
    """
    Run the assessment's required demonstration.

    This demonstration uses isolated local data so it does not
    modify the real inventory or the saved JSON file.
    """

    demo_resources = deepcopy(DEFAULT_RESOURCES)
    demo_fellows = deepcopy(DEFAULT_FELLOWS)
    demo_records = []

    def demo_find_resource(resource_id):
        for resource in demo_resources:
            if resource["id"] == resource_id:
                return resource
        return None

    def demo_find_loan(fellow_id, resource_id):
        for record in demo_records:
            if (
                record["fellow_id"] == fellow_id
                and record["resource_id"] == resource_id
            ):
                return record
        return None

    def demo_borrow(fellow_id, resource_id, quantity):
        resource = demo_find_resource(resource_id)

        if resource is None:
            print("Rejected: Resource not found.")
            return False

        if quantity <= 0:
            print("Rejected: Quantity must be greater than zero.")
            return False

        if quantity > resource["available"]:
            print(
                f"Rejected: Only {resource['available']} "
                f"{resource['name']}(s) are available."
            )
            return False

        resource["available"] -= quantity

        existing = demo_find_loan(fellow_id, resource_id)

        if existing:
            existing["quantity"] += quantity
        else:
            demo_records.append(
                {
                    "fellow_id": fellow_id,
                    "resource_id": resource_id,
                    "quantity": quantity,
                }
            )

        print(
            f"Success: {demo_fellows[fellow_id]} borrowed "
            f"{quantity} unit(s) of {resource['name']}."
        )

        return True

    def demo_return(fellow_id, resource_id, quantity):
        resource = demo_find_resource(resource_id)
        loan = demo_find_loan(fellow_id, resource_id)

        if resource is None or loan is None:
            print("Rejected: No active loan found.")
            return False

        if quantity <= 0:
            print("Rejected: Quantity must be greater than zero.")
            return False

        if quantity > loan["quantity"]:
            print(
                f"Rejected: {demo_fellows[fellow_id]} only has "
                f"{loan['quantity']} unit(s) of "
                f"{resource['name']} on loan."
            )
            return False

        resource["available"] += quantity
        loan["quantity"] -= quantity

        if loan["quantity"] == 0:
            demo_records.remove(loan)

        print(
            f"Success: {demo_fellows[fellow_id]} returned "
            f"{quantity} unit(s) of {resource['name']}."
        )

        return True

    print()
    print("========================================")
    print("       REQUIRED DEMONSTRATION")
    print("========================================")

    print()
    print("1. F001 borrows 2 laptops.")
    demo_borrow("F001", "R001", 2)

    print()
    print("2. F002 borrows 3 keyboards.")
    demo_borrow("F002", "R002", 3)

    print()
    print("3. F001 returns 1 laptop.")
    demo_return("F001", "R001", 1)

    print()
    print("4. F003 requests 4 headsets.")
    demo_borrow("F003", "R003", 4)

    print()
    print("5. F002 tries to return 4 keyboards.")
    demo_return("F002", "R002", 4)

    print()
    print("6. Search for LAPtop.")

    results = [
        resource
        for resource in demo_resources
        if "laptop" in resource["name"].lower()
    ]

    for resource in results:
        print(f"Found: {resource['name']} ({resource['id']})")

    print()
    print("7. Generate report.")

    total_units = sum(
        resource["total"]
        for resource in demo_resources
    )

    available_units = sum(
        resource["available"]
        for resource in demo_resources
    )

    borrowed_units = total_units - available_units

    low_stock = [
        resource
        for resource in demo_resources
        if resource["available"] < 3
    ]

    borrowed_by_resource = {
        resource["id"]:
        resource["total"] - resource["available"]
        for resource in demo_resources
    }

    highest_borrowed = max(borrowed_by_resource.values())

    most_borrowed = [
        resource
        for resource in demo_resources
        if borrowed_by_resource[resource["id"]] == highest_borrowed
        and highest_borrowed > 0
    ]

    print()
    print("--- Inventory Report ---")
    print(f"Total units: {total_units}")
    print(f"Available units: {available_units}")
    print(f"Units currently borrowed: {borrowed_units}")

    print()
    print("Low stock resources:")

    for resource in low_stock:
        print(
            f"{resource['name']} "
            f"({resource['available']} available)"
        )

    print()
    print("Most borrowed resource:")

    for resource in most_borrowed:
        print(
            f"{resource['name']} "
            f"({borrowed_by_resource[resource['id']]})"
        )


# ============================================================
# EDGE-CASE TESTS
# ============================================================

def run_edge_case_tests():
    """
    Run robustness and JSON persistence tests.

    The live application state is restored after all tests.
    """

    global resources
    global fellows
    global borrow_records

    print()
    print("========================================")
    print("          HIDDEN EDGE-CASE TESTS")
    print("========================================")

    original_resources = deepcopy(resources)
    original_fellows = deepcopy(fellows)
    original_borrow_records = deepcopy(borrow_records)

    passed = 0
    failed = 0

    def check(condition, success_message, failure_message):
        nonlocal passed, failed

        if condition:
            print(f"PASS: {success_message}")
            passed += 1
        else:
            print(f"FAIL: {failure_message}")
            failed += 1

    try:
        # ----------------------------------------------------
        # 1. Duplicate borrowing merges into one loan.
        # ----------------------------------------------------

        resources = deepcopy(DEFAULT_RESOURCES)
        fellows = deepcopy(DEFAULT_FELLOWS)
        borrow_records = []

        borrow_item("F001", "R001", 2)
        borrow_item("F001", "R001", 3)

        loan = find_loan("F001", "R001")

        check(
            loan is not None
            and loan["quantity"] == 5
            and resources[0]["available"] == 5
            and len(borrow_records) == 1,
            "Duplicate borrowing is merged into one loan",
            "Duplicate borrowing was not merged correctly",
        )

        # ----------------------------------------------------
        # 2. Partial return.
        # ----------------------------------------------------

        return_item("F001", "R001", 2)

        loan = find_loan("F001", "R001")

        check(
            loan is not None
            and loan["quantity"] == 3
            and resources[0]["available"] == 7,
            "Partial return updates loan and availability",
            "Partial return did not update state correctly",
        )

        # ----------------------------------------------------
        # 3. Full return removes loan.
        # ----------------------------------------------------

        return_item("F001", "R001", 3)

        check(
            find_loan("F001", "R001") is None
            and resources[0]["available"] == 10,
            "Full return removes the active loan",
            "Full return did not remove the active loan",
        )

        # ----------------------------------------------------
        # 4. Repeated return rejected.
        # ----------------------------------------------------

        before_resources = deepcopy(resources)
        before_records = deepcopy(borrow_records)

        success, _ = return_item("F001", "R001", 1)

        check(
            not success
            and resources == before_resources
            and borrow_records == before_records,
            "Repeated return is rejected without mutation",
            "Repeated return changed application state",
        )

        # ----------------------------------------------------
        # 5. Exact stock borrowing.
        # ----------------------------------------------------

        success, _ = borrow_item("F001", "R001", 10)

        check(
            success
            and resources[0]["available"] == 0,
            "Borrowing exactly all available stock succeeds",
            "Exact-stock borrowing failed",
        )

        # ----------------------------------------------------
        # 6. Exact-stock return.
        # ----------------------------------------------------

        success, _ = return_item("F001", "R001", 10)

        check(
            success
            and resources[0]["available"] == 10
            and find_loan("F001", "R001") is None,
            "Returning exactly all borrowed stock succeeds",
            "Exact-stock return failed",
        )

        # ----------------------------------------------------
        # 7. Failed borrowing does not mutate state.
        # ----------------------------------------------------

        before_resources = deepcopy(resources)
        before_records = deepcopy(borrow_records)

        success, _ = borrow_item("F001", "R001", 999)

        check(
            not success
            and resources == before_resources
            and borrow_records == before_records,
            "Failed borrowing does not mutate state",
            "Failed borrowing changed application state",
        )

        # ----------------------------------------------------
        # 8. Tied most-borrowed resources.
        # ----------------------------------------------------

        resources = [
            {
                "id": "R001",
                "name": "Laptop",
                "category": "Electronics",
                "total": 10,
                "available": 5,
            },
            {
                "id": "R002",
                "name": "Keyboard",
                "category": "Accessories",
                "total": 10,
                "available": 5,
            },
        ]

        fellows = deepcopy(DEFAULT_FELLOWS)

        borrow_records = [
            {
                "fellow_id": "F001",
                "resource_id": "R001",
                "quantity": 5,
            },
            {
                "fellow_id": "F002",
                "resource_id": "R002",
                "quantity": 5,
            },
        ]

        borrowed = calculate_borrowed_by_resource()

        leaders = [
            resource["id"]
            for resource in resources
            if borrowed[resource["id"]] == max(borrowed.values())
        ]

        check(
            leaders == ["R001", "R002"],
            "Tied most-borrowed resources are all identified",
            "Tied most-borrowed resources were not all identified",
        )

        # ----------------------------------------------------
        # 9. Failed excessive return does not mutate state.
        # ----------------------------------------------------

        before_resources = deepcopy(resources)
        before_records = deepcopy(borrow_records)

        success, _ = return_item("F001", "R001", 6)

        check(
            not success
            and resources == before_resources
            and borrow_records == before_records,
            "Failed excessive return does not mutate state",
            "Failed excessive return changed application state",
        )

        # ====================================================
        # JSON PERSISTENCE TESTS
        # ====================================================

        print()
        print("----------------------------------------")
        print("       JSON PERSISTENCE TESTS")
        print("----------------------------------------")

        with tempfile.TemporaryDirectory() as temp_directory:
            test_file = os.path.join(
                temp_directory,
                "test_inventory_data.json",
            )

            # ------------------------------------------------
            # 10. Valid inventory can be saved.
            # ------------------------------------------------

            resources = deepcopy(DEFAULT_RESOURCES)
            fellows = deepcopy(DEFAULT_FELLOWS)
            borrow_records = []

            borrow_item("F001", "R001", 2)

            saved, _ = save_data(test_file)

            check(
                saved and os.path.exists(test_file),
                "Valid inventory can be saved",
                "Valid inventory could not be saved",
            )

            # ------------------------------------------------
            # 11. Saved JSON is readable.
            # ------------------------------------------------

            json_readable = False

            try:
                with open(test_file, "r", encoding="utf-8") as file:
                    loaded_json = json.load(file)

                json_readable = isinstance(loaded_json, dict)

            except (OSError, json.JSONDecodeError):
                json_readable = False

            check(
                json_readable,
                "Saved JSON file is readable",
                "Saved JSON file could not be read",
            )

            # ------------------------------------------------
            # 12. Saved inventory can be loaded correctly.
            # ------------------------------------------------

            resources = []
            fellows = {}
            borrow_records = []

            loaded, _ = load_data(test_file)

            check(
                loaded
                and len(resources) == 3
                and fellows["F001"] == "Ada"
                and find_loan("F001", "R001")["quantity"] == 2
                and find_resource("R001")["available"] == 8,
                "Saved inventory can be loaded correctly",
                "Saved inventory could not be loaded correctly",
            )

            # ------------------------------------------------
            # 13. Missing JSON handled safely.
            # ------------------------------------------------

            missing_file = os.path.join(
                temp_directory,
                "missing.json",
            )

            loaded, _ = load_data(missing_file)

            check(
                not loaded,
                "Missing JSON file is handled safely",
                "Missing JSON file was not handled safely",
            )

            # ------------------------------------------------
            # 14. Malformed JSON does not corrupt live state.
            # ------------------------------------------------

            resources = deepcopy(DEFAULT_RESOURCES)
            fellows = deepcopy(DEFAULT_FELLOWS)
            borrow_records = []

            malformed_file = os.path.join(
                temp_directory,
                "malformed.json",
            )

            with open(
                malformed_file,
                "w",
                encoding="utf-8",
            ) as file:
                file.write("{ invalid json")

            before_resources = deepcopy(resources)
            before_fellows = deepcopy(fellows)
            before_records = deepcopy(borrow_records)

            loaded, _ = load_data(malformed_file)

            check(
                not loaded
                and resources == before_resources
                and fellows == before_fellows
                and borrow_records == before_records,
                "Malformed JSON does not corrupt live state",
                "Malformed JSON changed live state",
            )

            # ------------------------------------------------
            # 15. Invalid JSON structure rejected safely.
            # ------------------------------------------------

            invalid_structure_file = os.path.join(
                temp_directory,
                "invalid_structure.json",
            )

            with open(
                invalid_structure_file,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    {
                        "resources": [],
                        "fellows": {},
                    },
                    file,
                )

            loaded, _ = load_data(invalid_structure_file)

            check(
                not loaded,
                "Invalid JSON structure is rejected safely",
                "Invalid JSON structure was accepted",
            )

            # ------------------------------------------------
            # 16. Inconsistent inventory rejected.
            # ------------------------------------------------

            inconsistent_file = os.path.join(
                temp_directory,
                "inconsistent.json",
            )

            inconsistent_data = {
                "resources": [
                    {
                        "id": "R001",
                        "name": "Laptop",
                        "category": "Electronics",
                        "total": 10,
                        "available": 3,
                    }
                ],
                "fellows": {
                    "F001": "Ada"
                },
                "borrow_records": [],
            }

            with open(
                inconsistent_file,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(inconsistent_data, file)

            loaded, _ = load_data(inconsistent_file)

            check(
                not loaded,
                "Inconsistent inventory totals are rejected",
                "Inconsistent inventory totals were accepted",
            )

            # ------------------------------------------------
            # 17. Duplicate active loans rejected.
            # ------------------------------------------------

            duplicate_loan_file = os.path.join(
                temp_directory,
                "duplicate_loans.json",
            )

            duplicate_loan_data = {
                "resources": [
                    {
                        "id": "R001",
                        "name": "Laptop",
                        "category": "Electronics",
                        "total": 10,
                        "available": 5,
                    }
                ],
                "fellows": {
                    "F001": "Ada"
                },
                "borrow_records": [
                    {
                        "fellow_id": "F001",
                        "resource_id": "R001",
                        "quantity": 2,
                    },
                    {
                        "fellow_id": "F001",
                        "resource_id": "R001",
                        "quantity": 3,
                    },
                ],
            }

            with open(
                duplicate_loan_file,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(duplicate_loan_data, file)

            loaded, _ = load_data(duplicate_loan_file)

            check(
                not loaded,
                "Duplicate active loan records are rejected",
                "Duplicate active loan records were accepted",
            )

    finally:
        # Always restore the user's actual application state.
        resources = original_resources
        fellows = original_fellows
        borrow_records = original_borrow_records

    print()
    print("----------------------------------------")
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")

    if failed == 0:
        print("RESULT: ALL EDGE-CASE TESTS PASSED.")
    else:
        print("RESULT: SOME EDGE-CASE TESTS FAILED.")

    print("----------------------------------------")
    print("Live application state restored.")


# ============================================================
# MENU
# ============================================================

def display_menu():
    """Display the main application menu."""

    print()
    print("========================================")
    print("       RESOURCE INVENTORY SYSTEM")
    print("========================================")
    print("1. Add resource")
    print("2. List resources")
    print("3. Borrow resource")
    print("4. Return resource")
    print("5. Search resources")
    print("6. Filter by category")
    print("7. Generate report")
    print("8. Run required demonstration")
    print("9. Run hidden edge-case tests")
    print("10. Exit")


def main_menu():
    """Run the main application loop."""

    initialize_data()

    while True:
        display_menu()

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            add_resource()

        elif choice == "2":
            list_resources()

        elif choice == "3":
            borrow_resource()

        elif choice == "4":
            return_resource()

        elif choice == "5":
            search_resources_menu()

        elif choice == "6":
            filter_category_menu()

        elif choice == "7":
            generate_report()

        elif choice == "8":
            run_required_demonstration()

        elif choice == "9":
            run_edge_case_tests()

        elif choice == "10":
            saved, message = save_data()

            if saved:
                print()
                print("Final inventory data saved successfully.")
            else:
                print()
                print(f"Warning: Final inventory save failed: {message}")

            print("Thank you for using the Resource Inventory System.")
            break

        else:
            print("Invalid choice. Please enter a number from 1 to 10.")


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main_menu()
