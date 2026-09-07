TIME_WINDOW_HOURS = 36
TIME_WINDOW_SECONDS = TIME_WINDOW_HOURS * 3600

LOCATION = "India"

POOLS = {
    "Tech (Web Dev / SDE / AI-ML)": [
        "Web Developer Intern",
        "Software Engineer Intern",
        "SDE Intern",
        "Machine Learning Intern",
        "AI Intern",
        "Data Science Intern",
    ],
    "Business (Product / BD / Marketing)": [
        "Product Management Intern",
        "Business Development Intern",
        "Marketing Intern",
        "Growth Intern",
    ],
}

RAW_PER_POOL = 50

FINAL_PER_POOL = 5

DETAIL_CHECK_TOP_N = 15

PRIORITIZE_EXTERNAL_APPLY = True

SHEET_TAB_NAME = "Internships"
SHEET_HEADERS = [
    "Date Added (IST)",
    "Pool",
    "Title",
    "Company",
    "Location",
    "Posted",
    "About the Role",
    "Apply Type",
    "Job URL",
    "Job ID",
]

DESCRIPTION_MAX_CHARS = 400

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 15
REQUEST_DELAY_SECONDS = 1.5  # polite delay between requests to reduce block risk
MAX_RETRIES = 3
