import streamlit as st
import pandas as pd
from datetime import date
import os
import streamlit_authenticator as stauth


# ===== User Authentication =====
hashed_passwords = stauth.Hasher().hash_list(["12345"])

credentials = {
    "usernames": {
        "bright": {
            "name": "Bright Lin",
            "password": hashed_passwords[0],
        }
    }
}

authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="job_tracker_cookie", 
    key="abcdef", 
    cookie_expiry_days=0
)

# --- Authentication Logic ---
# Get login status from session_state
auth_status = st.session_state.get("authentication_status")

if auth_status is None:
    name, auth_status, username = authenticator.login("main", "Job Tracker Login")

if auth_status:
    # user logged in

    # Log Out Button
    authenticator.logout("Logout", "sidebar")

    name = st.session_state.get("name")
    username = st.session_state.get("username")
    st.sidebar.success(f"Welcome, {name}!")
    
    # App Content Under Here
    st.title("📌 Job Application Tracker")
    st.write("✅ You are logged in — your job tracker is now active.")


















    # (Job tracker logic is below this section)

    DATA_FILE = "jobs.csv"

    def load_jobs():
        if os.path.exists(DATA_FILE):
            return pd.read_csv(DATA_FILE)
        else:
            return pd.DataFrame(columns=["Title", "Company", "Location", "Status", "Date Applied", "Notes", "URL"])

    def save_jobs(df):
        df.to_csv(DATA_FILE, index=False)


    # ---- config ----
    st.set_page_config(page_title="Job Application Tracker", layout="wide")

    # load existing jobs
    jobs_df = load_jobs()

    st.sidebar.header("Add New Job")

    # === ADD JOB ===
    # widget keys
    INPUT_KEYS = {
        "title": "title",
        "company": "company",
        "location": "location",
        "status": "status",
        "date_applied": "date_applied",
        "notes": "notes",
        "url": "url",
        "feedback": "form_feedback"
    }

    # ensure keys exist with sensible defaults
    if INPUT_KEYS["status"] not in st.session_state:
        st.session_state[INPUT_KEYS["status"]] = "Applied"
    if INPUT_KEYS["date_applied"] not in st.session_state:
        st.session_state[INPUT_KEYS["date_applied"]] = date.today()
    if INPUT_KEYS["feedback"] not in st.session_state:
        st.session_state[INPUT_KEYS["feedback"]] = ""

    def submit_callback():
        #Read widget keys, append to CSV, clear keys, set feedback
        title = st.session_state.get(INPUT_KEYS["title"], "").strip()
        company = st.session_state.get(INPUT_KEYS["company"], "").strip()

        if not title or not company:
            st.session_state[INPUT_KEYS["feedback"]] = ("warning", "Please enter at least a job title and company.")
            return

        row = {
            "Title": title,
            "Company": company,
            "Location": st.session_state.get(INPUT_KEYS["location"], ""),
            "Status": st.session_state.get(INPUT_KEYS["status"], "Applied"),
            "Date Applied": st.session_state.get(INPUT_KEYS["date_applied"], str(date.today())),
            "Notes": st.session_state.get(INPUT_KEYS["notes"], ""),
            "URL": st.session_state.get(INPUT_KEYS["url"], "")
        }

        # append and save
        df = load_jobs()
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        save_jobs(df)

        # clear the widget keys
        st.session_state[INPUT_KEYS["title"]] = ""
        st.session_state[INPUT_KEYS["company"]] = ""
        st.session_state[INPUT_KEYS["location"]] = ""
        st.session_state[INPUT_KEYS["status"]] = "Applied"
        st.session_state[INPUT_KEYS["date_applied"]] = date.today()
        st.session_state[INPUT_KEYS["notes"]] = ""
        st.session_state[INPUT_KEYS["url"]] = ""
        st.session_state[INPUT_KEYS["feedback"]] = ("success", f"Added job: {title} at {company}")

    # Build the form — widgets must use the keys from submit_callback function
    with st.sidebar.form("Add Job Form"):
        st.text_input("Job Title", key=INPUT_KEYS["title"])
        st.text_input("Company", key=INPUT_KEYS["company"])
        st.text_input("Location", key=INPUT_KEYS["location"])
        st.selectbox("Status", ["Applied", "Interview", "Offer", "Rejected"], key=INPUT_KEYS["status"])
        st.date_input("Date Applied", value=st.session_state[INPUT_KEYS["date_applied"]], key=INPUT_KEYS["date_applied"])
        st.text_area("Notes", key=INPUT_KEYS["notes"])
        st.text_input("Job URL", key=INPUT_KEYS["url"])

        # Callback here — it runs before re-render and can clear keys safely
        st.form_submit_button("Add Job", on_click=submit_callback)

    # Show feedback if set
    feedback = st.session_state.get(INPUT_KEYS["feedback"], "")
    if feedback:
        level, msg = feedback
        if level == "success":
            st.success(msg)
        elif level == "warning":
            st.warning(msg)
        else:
            st.info(msg)


    # ===== SEARCH & FILTER & VIEW =====
    st.text_input("Search", placeholder="Company Name")

    st.sidebar.header("Filter Jobs")
    status_filter = st.sidebar.multiselect("Filter by Status",
                                        ["Applied", "Interview", "Offer", "Rejected"],
                                        default=["Applied", "Interview", "Offer", "Rejected"])
    company_filter = st.sidebar.text_input("Filter by Company")

    # ensures string types so .str works
    for col in ["Title", "Company", "Location"]:
        jobs_df[col] = jobs_df[col].astype(str)

    filtered_df = jobs_df[
        (jobs_df["Status"].isin(status_filter)) &
        (jobs_df["Company"].str.contains(company_filter, case=False, na=False))
    ]

    st.subheader(f"All Jobs ({len(filtered_df)})")

    # Nmaes the Columns
    display_df = filtered_df.rename(columns={
        "Title": "Title",
        "Date Applied": "Date",
        "URL": "Link"
    })[["Title", "Company", "Location", "Status", "Date", "Notes", "Link"]]

    st.dataframe(display_df, width='stretch')


    # =====  Export =====
    st.sidebar.header("Export Data")
    if st.sidebar.button("Export to Excel"):
        filtered_df.to_excel("jobs_export.xlsx", index=False)
        st.sidebar.success("Exported to jobs_export.xlsx")


    # ===== Delete =====
    st.sidebar.header("Delete Job")
    if not jobs_df.empty:
        delete_index = st.sidebar.number_input("Row Index to Delete (from top of table)",
                                            min_value=0, max_value=len(jobs_df)-1, step=1)
        if st.sidebar.button("Delete Job"):
            removed = jobs_df.iloc[delete_index]
            jobs_df = jobs_df.drop(delete_index).reset_index(drop=True)
            save_jobs(jobs_df)
            st.sidebar.success(f"Deleted job: {removed['Title']} at {removed['Company']}")














elif auth_status is False:
    st.error("❌ Username/password is incorrect")
else:
    st.warning("🔐 Please log in to access your job tracker.")






