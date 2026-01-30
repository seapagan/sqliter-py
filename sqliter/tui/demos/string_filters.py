"""String Filter demos."""

from __future__ import annotations

import io

from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code


def _run_startswith() -> str:
    """Filter strings that start with a specific prefix.

    Use __startswith to match records where a field begins with
    the specified value.
    """
    output = io.StringIO()

    class User(BaseDBModel):
        username: str

    db = SqliterDB(memory=True)
    db.create_table(User)

    db.insert(User(username="alice_wonder"))
    db.insert(User(username="alice_smith"))
    db.insert(User(username="bob_builder"))

    # Find usernames starting with "alice"
    results = db.select(User).filter(username__startswith="alice").fetch_all()
    output.write(f"Users starting with 'alice': {len(results)}\n")
    for user in results:
        output.write(f"  - {user.username}\n")

    db.close()
    return output.getvalue()


def _run_endswith() -> str:
    """Filter strings that end with a specific suffix.

    Use __endswith to match records where a field ends with
    the specified value.
    """
    output = io.StringIO()

    class File(BaseDBModel):
        filename: str

    db = SqliterDB(memory=True)
    db.create_table(File)

    db.insert(File(filename="document.txt"))
    db.insert(File(filename="image.png"))
    db.insert(File(filename="notes.txt"))
    db.insert(File(filename="data.csv"))

    # Find files ending with ".txt"
    results = db.select(File).filter(filename__endswith=".txt").fetch_all()
    output.write(f"Text files: {len(results)}\n")
    for file in results:
        output.write(f"  - {file.filename}\n")

    db.close()
    return output.getvalue()


def _run_contains() -> str:
    """Filter strings that contain a specific substring.

    Use __contains to match records where a field contains
    the specified value anywhere within it.
    """
    output = io.StringIO()

    class Product(BaseDBModel):
        name: str

    db = SqliterDB(memory=True)
    db.create_table(Product)

    db.insert(Product(name="Apple iPhone"))
    db.insert(Product(name="Samsung Galaxy"))
    db.insert(Product(name="Apple iPad"))
    db.insert(Product(name="Google Pixel"))

    # Find products containing "Apple"
    results = db.select(Product).filter(name__contains="Apple").fetch_all()
    output.write(f"Products containing 'Apple': {len(results)}\n")
    for product in results:
        output.write(f"  - {product.name}\n")

    db.close()
    return output.getvalue()


def _run_case_insensitive() -> str:
    """Filter strings ignoring case with __istartswith and __iendswith.

    Use case-insensitive operators to match strings regardless of
    capitalization.
    """
    output = io.StringIO()

    class User(BaseDBModel):
        email: str

    db = SqliterDB(memory=True)
    db.create_table(User)

    db.insert(User(email="ALICE@example.com"))
    db.insert(User(email="bob@EXAMPLE.com"))
    db.insert(User(email="charlie@test.com"))

    # Find emails ending with "@example.com" (case-insensitive)
    results = (
        db.select(User).filter(email__iendswith="@example.com").fetch_all()
    )
    output.write(f"Emails ending with '@example.com': {len(results)}\n")
    for user in results:
        output.write(f"  - {user.email}\n")

    # Find emails starting with "BOB" (case-insensitive)
    bob_results = db.select(User).filter(email__istartswith="BOB").fetch_all()
    output.write(f"\nEmails starting with 'BOB': {len(bob_results)}\n")
    for user in bob_results:
        output.write(f"  - {user.email}\n")

    db.close()
    return output.getvalue()


def _run_icontains() -> str:
    """Filter strings containing a substring, ignoring case.

    Use __icontains for case-insensitive substring matching.
    """
    output = io.StringIO()

    class Article(BaseDBModel):
        title: str

    db = SqliterDB(memory=True)
    db.create_table(Article)

    db.insert(Article(title="Python Programming Guide"))
    db.insert(Article(title="Advanced PYTHON Techniques"))
    db.insert(Article(title="Web Development"))
    db.insert(Article(title="python for Beginners"))

    # Find articles containing "python" (case-insensitive)
    results = db.select(Article).filter(title__icontains="python").fetch_all()
    output.write(f"Articles containing 'python': {len(results)}\n")
    for article in results:
        output.write(f"  - {article.title}\n")

    db.close()
    return output.getvalue()


def get_category() -> DemoCategory:
    """Get the String Filters demo category."""
    return DemoCategory(
        id="string_filters",
        title="String Filters",
        icon="",
        demos=[
            Demo(
                id="string_startswith",
                title="Starts With (__startswith)",
                description="Match strings starting with prefix",
                category="string_filters",
                code=extract_demo_code(_run_startswith),
                execute=_run_startswith,
            ),
            Demo(
                id="string_endswith",
                title="Ends With (__endswith)",
                description="Match strings ending with suffix",
                category="string_filters",
                code=extract_demo_code(_run_endswith),
                execute=_run_endswith,
            ),
            Demo(
                id="string_contains",
                title="Contains (__contains)",
                description="Match strings containing substring",
                category="string_filters",
                code=extract_demo_code(_run_contains),
                execute=_run_contains,
            ),
            Demo(
                id="string_case_insensitive",
                title="Case-Insensitive (__i*)",
                description="Match strings ignoring case",
                category="string_filters",
                code=extract_demo_code(_run_case_insensitive),
                execute=_run_case_insensitive,
            ),
            Demo(
                id="string_icontains",
                title="Contains Case-Insensitive",
                description="Match substring ignoring case",
                category="string_filters",
                code=extract_demo_code(_run_icontains),
                execute=_run_icontains,
            ),
        ],
    )
