resources = [
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

fellows = {
    "F001": "Ada",
    "F002": "John",
    "F003": "Grace",
}

borrow_records = []


# ============================================================
# LOOKUP FUNCTIONS
# ============================================================

def find_resource(resource_id):
    """Return a resource by ID, or None if it does not exist."""
    resource_id = resource_id.strip().upper()

    for resource in resources:
        if resource["id"].upper() == resource_id:
            return resource

    return None


def find_fellow(fellow_id):
    """Return a fellow's name by ID, or None if not found."""
    fellow_id = fellow_id.strip().upper()

    for stored_id, name in fellows.items():
        if stored_id.upper() == fellow_id:
            return name

    return None


def find_fellow_id(fellow_id):
    """Return the stored fellow ID matching the supplied ID."""
    fellow_id = fellow_id.strip().upper()

    for stored_id in fellows:
        if stored_id.upper() == fellow_id:
            return stored_id

    return None


# ============================================================
# DISPLAY FUNCTIONS
# ============================================================

def display_resource(resource):
    """Display one resource in a consistent format."""
    print(
        f'{resource["id"]} | '
        f'{resource["name"]} | '
        f'{resource["category"]} | '
        f'Total: {resource["total"]} | '
        f'Available: {resource["available"]}'
    )


def list_resources():
    """Display all resources in the inventory."""
    print("\n--- Resource Inventory ---")

    if not resources:
        print("No resources in the inventory.")
        return

    for resource in resources:
        display_resource(resource)


# ============================================================
# RESOURCE MANAGEMENT
# ============================================================

def add_resource():
    """Add a new resource after validating all input."""
    print("\n--- Add Resource ---")

    resource_id = input("Enter resource ID: ").strip()

    if not resource_id:
        print("Error: Resource ID cannot be empty.")
        return

    if find_resource(resource_id) is not None:
        print("Error: A resource with that ID already exists.")
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

    resources.append(
        {
            "id": resource_id.upper(),
            "name": name,
            "category": category,
            "total": total,
            "available": total,
        }
    )

    print(f"Resource '{name}' added successfully.")


# ============================================================
# BORROWING
# ============================================================

def borrow_item(fellow_id, resource_id, quantity):
    """
    Perform the core borrowing operation.

    If the fellow already has the resource on loan, the new
    quantity is added to the existing loan record.

    Returns:
        tuple: (success, message)
    """
    stored_fellow_id = find_fellow_id(fellow_id)

    if stored_fellow_id is None:
        return False, "Fellow ID not found."

    resource = find_resource(resource_id)

    if resource is None:
        return False, "Resource ID not found."

    if not isinstance(quantity, int) or isinstance(quantity, bool):
        return False, "Quantity must be a whole number."

    if quantity <= 0:
        return False, "Quantity must be greater than zero."

    if quantity > resource["available"]:
        return (
            False,
            f'Only {resource["available"]} '
            f'{resource["name"]}(s) are available.',
        )

    # --------------------------------------------------------
    # State changes happen only after all validation succeeds.
    # --------------------------------------------------------

    resource["available"] -= quantity

    # Look for an existing active loan for this fellow/resource.
    existing_loan = None

    for record in borrow_records:
        if (
            record["fellow_id"] == stored_fellow_id
            and record["resource_id"] == resource["id"]
        ):
            existing_loan = record
            break

    if existing_loan is not None:
        existing_loan["quantity"] += quantity
    else:
        borrow_records.append(
            {
                "fellow_id": stored_fellow_id,
                "resource_id": resource["id"],
                "quantity": quantity,
            }
        )

    fellow_name = fellows[stored_fellow_id]

    return (
        True,
        f'{fellow_name} successfully borrowed '
        f'{quantity} unit(s) of {resource["name"]}.',
    )


def borrow_resource():
    """Collect input and perform a borrowing operation."""
    print("\n--- Borrow Resource ---")

    fellow_id = input("Enter fellow ID: ").strip()

    if find_fellow_id(fellow_id) is None:
        print("Error: Fellow ID not found.")
        return

    resource_id = input("Enter resource ID: ").strip()

    if find_resource(resource_id) is None:
        print("Error: Resource ID not found.")
        return

    quantity_input = input("Enter quantity to borrow: ").strip()

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

    if success:
        print(message)
    else:
        print(f"Error: {message}")


# ============================================================
# RETURNS
# ============================================================

def find_loan(fellow_id, resource_id):
    """Return an active loan record for a fellow/resource pair."""
    stored_fellow_id = find_fellow_id(fellow_id)
    resource = find_resource(resource_id)

    if stored_fellow_id is None or resource is None:
        return None

    for record in borrow_records:
        if (
            record["fellow_id"] == stored_fellow_id
            and record["resource_id"] == resource["id"]
        ):
            return record

    return None


def return_item(fellow_id, resource_id, quantity):
    """
    Perform the core return operation.

    Returns:
        tuple: (success, message)
    """
    stored_fellow_id = find_fellow_id(fellow_id)

    if stored_fellow_id is None:
        return False, "Fellow ID not found."

    resource = find_resource(resource_id)

    if resource is None:
        return False, "Resource ID not found."

    if not isinstance(quantity, int) or isinstance(quantity, bool):
        return False, "Quantity must be a whole number."

    if quantity <= 0:
        return False, "Quantity must be greater than zero."

    loan_record = find_loan(
        stored_fellow_id,
        resource["id"],
    )

    fellow_name = fellows[stored_fellow_id]

    if loan_record is None:
        return (
            False,
            f'{fellow_name} does not currently have '
            f'{resource["name"]} on loan.',
        )

    if quantity > loan_record["quantity"]:
        return (
            False,
            f'{fellow_name} only has '
            f'{loan_record["quantity"]} unit(s) of '
            f'{resource["name"]} on loan.',
        )

    # State changes happen only after every validation succeeds.
    loan_record["quantity"] -= quantity
    resource["available"] += quantity

    if loan_record["quantity"] == 0:
        borrow_records.remove(loan_record)

    return (
        True,
        f'{fellow_name} successfully returned '
        f'{quantity} unit(s) of {resource["name"]}.',
    )


def return_resource():
    """Collect input and perform a return operation."""
    print("\n--- Return Resource ---")

    fellow_id = input("Enter fellow ID: ").strip()

    if find_fellow_id(fellow_id) is None:
        print("Error: Fellow ID not found.")
        return

    resource_id = input("Enter resource ID: ").strip()

    if find_resource(resource_id) is None:
        print("Error: Resource ID not found.")
        return

    quantity_input = input("Enter quantity to return: ").strip()

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

    if success:
        print(message)
    else:
        print(f"Error: {message}")


# ============================================================
# SEARCH AND FILTER
# ============================================================

def search_resources():
    """Search resources by name without considering letter case."""
    print("\n--- Search Resources ---")

    search_term = input(
        "Enter resource name to search: "
    ).strip().lower()

    if not search_term:
        print("Error: Search term cannot be empty.")
        return

    matches = [
        resource
        for resource in resources
        if search_term in resource["name"].lower()
    ]

    if not matches:
        print("No resources found.")
        return

    print("\nSearch results:")

    for resource in matches:
        display_resource(resource)


def filter_by_category():
    """Display resources belonging to a category."""
    print("\n--- Filter by Category ---")

    category = input("Enter category: ").strip().lower()

    if not category:
        print("Error: Category cannot be empty.")
        return

    matches = [
        resource
        for resource in resources
        if resource["category"].lower() == category
    ]

    if not matches:
        print("No resources found in that category.")
        return

    print("\nCategory results:")

    for resource in matches:
        display_resource(resource)


# ============================================================
# REPORTING
# ============================================================

def calculate_borrowed_by_resource():
    """Return total currently borrowed units grouped by resource."""
    borrowed_by_resource = {}

    for record in borrow_records:
        resource_id = record["resource_id"]

        borrowed_by_resource[resource_id] = (
            borrowed_by_resource.get(resource_id, 0)
            + record["quantity"]
        )

    return borrowed_by_resource


def generate_report():
    """Generate an inventory and borrowing report."""
    print("\n--- Inventory Report ---")

    total_units = sum(
        resource["total"]
        for resource in resources
    )

    available_units = sum(
        resource["available"]
        for resource in resources
    )

    borrowed_units = sum(
        record["quantity"]
        for record in borrow_records
    )

    print(f"Total units: {total_units}")
    print(f"Available units: {available_units}")
    print(f"Units currently borrowed: {borrowed_units}")

    low_stock_resources = [
        resource
        for resource in resources
        if resource["available"] < 3
    ]

    print("\nLow stock resources:")

    if low_stock_resources:
        for resource in low_stock_resources:
            print(
                f'{resource["name"]} '
                f'({resource["available"]} available)'
            )
    else:
        print("None")

    borrowed_by_resource = calculate_borrowed_by_resource()

    print("\nMost borrowed resource:")

    if not borrowed_by_resource:
        print("No resources are currently borrowed.")
        return

    highest_borrowed = max(
        borrowed_by_resource.values()
    )

    leaders = []

    for resource_id, quantity in borrowed_by_resource.items():
        if quantity == highest_borrowed:
            resource = find_resource(resource_id)

            if resource is not None:
                leaders.append(
                    f'{resource["name"]} ({quantity})'
                )

    print(", ".join(leaders))


# ============================================================
# REQUIRED DEMONSTRATION
# ============================================================

def run_required_demonstration():
    """
    Run the exact assessment demonstration.

    The demonstration uses fresh local data so it does not
    depend on the user's previous menu activity.
    """
    print("\n========================================")
    print("       REQUIRED DEMONSTRATION")
    print("========================================")

    demo_resources = [
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

    demo_borrow_records = []

    def demo_find_resource(resource_id):
        resource_id = resource_id.strip().upper()

        for resource in demo_resources:
            if resource["id"].upper() == resource_id:
                return resource

        return None

    def demo_borrow(fellow_id, resource_id, quantity):
        resource = demo_find_resource(resource_id)

        if resource is None:
            print("Rejected: Resource ID not found.")
            return

        if quantity <= 0:
            print("Rejected: Quantity must be positive.")
            return

        if quantity > resource["available"]:
            print(
                f'Rejected: Only {resource["available"]} '
                f'{resource["name"]}(s) are available.'
            )
            return

        resource["available"] -= quantity

        existing_loan = None

        for record in demo_borrow_records:
            if (
                record["fellow_id"] == fellow_id
                and record["resource_id"] == resource["id"]
            ):
                existing_loan = record
                break

        if existing_loan is not None:
            existing_loan["quantity"] += quantity
        else:
            demo_borrow_records.append(
                {
                    "fellow_id": fellow_id,
                    "resource_id": resource["id"],
                    "quantity": quantity,
                }
            )

        print(
            f'Success: {fellows[fellow_id]} borrowed '
            f'{quantity} unit(s) of {resource["name"]}.'
        )

    def demo_return(fellow_id, resource_id, quantity):
        resource = demo_find_resource(resource_id)

        if resource is None:
            print("Rejected: Resource ID not found.")
            return

        loan_record = None

        for record in demo_borrow_records:
            if (
                record["fellow_id"] == fellow_id
                and record["resource_id"] == resource["id"]
            ):
                loan_record = record
                break

        if loan_record is None:
            print(
                f'Rejected: {fellows[fellow_id]} does not currently '
                f'have {resource["name"]} on loan.'
            )
            return

        if quantity <= 0:
            print("Rejected: Quantity must be positive.")
            return

        if quantity > loan_record["quantity"]:
            print(
                f'Rejected: {fellows[fellow_id]} only has '
                f'{loan_record["quantity"]} unit(s) of '
                f'{resource["name"]} on loan.'
            )
            return

        loan_record["quantity"] -= quantity
        resource["available"] += quantity

        if loan_record["quantity"] == 0:
            demo_borrow_records.remove(loan_record)

        print(
            f'Success: {fellows[fellow_id]} returned '
            f'{quantity} unit(s) of {resource["name"]}.'
        )

    # 1. F001 borrows 2 laptops.
    print("\n1. F001 borrows 2 laptops.")
    demo_borrow("F001", "R001", 2)

    # 2. F002 borrows 3 keyboards.
    print("\n2. F002 borrows 3 keyboards.")
    demo_borrow("F002", "R002", 3)

    # 3. F001 returns 1 laptop.
    print("\n3. F001 returns 1 laptop.")
    demo_return("F001", "R001", 1)

    # 4. F003 requests 4 headsets.
    print("\n4. F003 requests 4 headsets.")
    demo_borrow("F003", "R003", 4)

    # 5. F002 tries to return 4 keyboards.
    print("\n5. F002 tries to return 4 keyboards.")
    demo_return("F002", "R002", 4)

    # 6. Search for LAPtop.
    print("\n6. Search for LAPtop.")

    search_term = "LAPtop".lower()

    for resource in demo_resources:
        if search_term in resource["name"].lower():
            print(
                f'Found: {resource["name"]} '
                f'({resource["id"]})'
            )

    # 7. Generate report.
    print("\n7. Generate report.")

    total_units = sum(
        resource["total"]
        for resource in demo_resources
    )

    available_units = sum(
        resource["available"]
        for resource in demo_resources
    )

    borrowed_units = sum(
        record["quantity"]
        for record in demo_borrow_records
    )

    print("\n--- Inventory Report ---")
    print(f"Total units: {total_units}")
    print(f"Available units: {available_units}")
    print(f"Units currently borrowed: {borrowed_units}")

    low_stock_resources = [
        resource
        for resource in demo_resources
        if resource["available"] < 3
    ]

    print("\nLow stock resources:")

    if low_stock_resources:
        for resource in low_stock_resources:
            print(
                f'{resource["name"]} '
                f'({resource["available"]} available)'
            )
    else:
        print("None")

    borrowed_by_resource = {}

    for record in demo_borrow_records:
        resource_id = record["resource_id"]

        borrowed_by_resource[resource_id] = (
            borrowed_by_resource.get(resource_id, 0)
            + record["quantity"]
        )

    print("\nMost borrowed resource:")

    if borrowed_by_resource:
        highest = max(
            borrowed_by_resource.values()
        )

        leaders = []

        for resource_id, quantity in borrowed_by_resource.items():
            if quantity == highest:
                resource = demo_find_resource(resource_id)

                if resource is not None:
                    leaders.append(
                        f'{resource["name"]} ({quantity})'
                    )

        print(", ".join(leaders))
    else:
        print("No resources are currently borrowed.")


# ============================================================
# HIDDEN EDGE-CASE TESTS
# ============================================================

def run_edge_case_tests():
    """
    Run internal tests for important inventory edge cases.

    The live application state is restored after the tests,
    whether the tests pass or fail.
    """
    from copy import deepcopy

    global resources
    global borrow_records

    original_resources = deepcopy(resources)
    original_borrow_records = deepcopy(borrow_records)

    print("\n========================================")
    print("          HIDDEN EDGE-CASE TESTS")
    print("========================================")

    passed = 0
    failed = 0

    def check(test_name, condition):
        nonlocal passed, failed

        if condition:
            print(f"PASS: {test_name}")
            passed += 1
        else:
            print(f"FAIL: {test_name}")
            failed += 1

    try:
        # ----------------------------------------------------
        # Start every test from clean assessment data.
        # ----------------------------------------------------
        resources = [
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

        borrow_records = []

        # ----------------------------------------------------
        # 1. Duplicate borrowing must merge.
        # ----------------------------------------------------
        success_1, _ = borrow_item("F001", "R001", 2)
        success_2, _ = borrow_item("F001", "R001", 3)

        laptop_loan = find_loan("F001", "R001")

        check(
            "Duplicate borrowing is merged into one loan",
            (
                success_1
                and success_2
                and laptop_loan is not None
                and laptop_loan["quantity"] == 5
                and len(borrow_records) == 1
            ),
        )

        # ----------------------------------------------------
        # 2. Partial return.
        # ----------------------------------------------------
        success, _ = return_item("F001", "R001", 2)
        laptop = find_resource("R001")
        laptop_loan = find_loan("F001", "R001")

        check(
            "Partial return updates loan and availability",
            (
                success
                and laptop["available"] == 7
                and laptop_loan is not None
                and laptop_loan["quantity"] == 3
            ),
        )

        # ----------------------------------------------------
        # 3. Full return.
        # ----------------------------------------------------
        success, _ = return_item("F001", "R001", 3)
        laptop = find_resource("R001")

        check(
            "Full return removes the active loan",
            (
                success
                and laptop["available"] == 10
                and find_loan("F001", "R001") is None
            ),
        )

        # ----------------------------------------------------
        # 4. Repeated return after full return.
        # ----------------------------------------------------
        before_resources = deepcopy(resources)
        before_records = deepcopy(borrow_records)

        success, message = return_item("F001", "R001", 1)

        check(
            "Repeated return is rejected without mutation",
            (
                not success
                and "does not currently have" in message
                and resources == before_resources
                and borrow_records == before_records
            ),
        )

        # ----------------------------------------------------
        # 5. Borrow exactly all available stock.
        # ----------------------------------------------------
        success, _ = borrow_item("F002", "R003", 3)
        headset = find_resource("R003")
        headset_loan = find_loan("F002", "R003")

        check(
            "Borrowing exactly all available stock succeeds",
            (
                success
                and headset["available"] == 0
                and headset_loan is not None
                and headset_loan["quantity"] == 3
            ),
        )

        # ----------------------------------------------------
        # 6. Return exactly all borrowed stock.
        # ----------------------------------------------------
        success, _ = return_item("F002", "R003", 3)
        headset = find_resource("R003")

        check(
            "Returning exactly all borrowed stock succeeds",
            (
                success
                and headset["available"] == 3
                and find_loan("F002", "R003") is None
            ),
        )

        # ----------------------------------------------------
        # 7. Failed operations must not mutate state.
        # ----------------------------------------------------
        before_resources = deepcopy(resources)
        before_records = deepcopy(borrow_records)

        success, _ = borrow_item("F003", "R003", 4)

        check(
            "Failed borrowing does not mutate state",
            (
                not success
                and resources == before_resources
                and borrow_records == before_records
            ),
        )

        # ----------------------------------------------------
        # 8. Tied most-borrowed resources.
        # ----------------------------------------------------
        borrow_item("F001", "R001", 2)
        borrow_item("F002", "R002", 2)

        borrowed_by_resource = calculate_borrowed_by_resource()

        highest = max(borrowed_by_resource.values())

        leaders = [
            resource_id
            for resource_id, quantity
            in borrowed_by_resource.items()
            if quantity == highest
        ]

        check(
            "Tied most-borrowed resources are all identified",
            (
                highest == 2
                and "R001" in leaders
                and "R002" in leaders
                and len(leaders) == 2
            ),
        )

        # ----------------------------------------------------
        # 9. Failed excessive return does not mutate state.
        # ----------------------------------------------------
        before_resources = deepcopy(resources)
        before_records = deepcopy(borrow_records)

        success, _ = return_item("F001", "R001", 3)

        check(
            "Failed excessive return does not mutate state",
            (
                not success
                and resources == before_resources
                and borrow_records == before_records
            ),
        )

        # ----------------------------------------------------
        # Final summary.
        # ----------------------------------------------------
        print("\n----------------------------------------")
        print(f"Tests passed: {passed}")
        print(f"Tests failed: {failed}")

        if failed == 0:
            print("RESULT: ALL EDGE-CASE TESTS PASSED.")
        else:
            print("RESULT: SOME EDGE-CASE TESTS FAILED.")

    finally:
        # Always restore the user's live application state.
        resources = original_resources
        borrow_records = original_borrow_records

        print("----------------------------------------")
        print("Live application state restored.")


# ============================================================
# MAIN MENU
# ============================================================

def main_menu():
    """Run the interactive resource inventory menu."""
    while True:
        print("\n========================================")
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
            search_resources()

        elif choice == "6":
            filter_by_category()

        elif choice == "7":
            generate_report()

        elif choice == "8":
            run_required_demonstration()

        elif choice == "9":
            run_edge_case_tests()

        elif choice == "10":
            print(
                "Thank you for using the Resource Inventory System."
            )
            break

        else:
            print(
                "Error: Invalid choice. Please select 1-10."
            )


if __name__ == "__main__":
    main_menu()