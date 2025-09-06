def admin_dashboard():
    st.title("Administrator Dashboard")

    # Role switcher
    view_as = st.radio("View app as:", ["Admin Full", "Student", "Instructor"], index=0)

    if view_as == "Admin Full":
        st.subheader("You are in full admin mode.")
        st.write("You can see both student and instructor dashboards together.")
        st.markdown("---")
        st.subheader("Student Dashboard")
        student_dashboard()
        st.markdown("---")
        st.subheader("Instructor Dashboard")
        instructor_dashboard()
    elif view_as == "Student":
        st.subheader("Viewing as Student")
        student_dashboard()
    elif view_as == "Instructor":
        st.subheader("Viewing as Instructor")
        instructor_dashboard()
