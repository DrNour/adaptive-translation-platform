import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from datetime import datetime
from db_utils import (
    init_db, register_user, validate_login, get_user_role,
    get_tasks, save_submission, get_submissions, get_idioms,
    add_idiom, delete_idiom, get_practice_bank, add_practice_item,
    assign_practices_to_user, get_student_practice, mark_practice_completed,
    load_heuristics, save_heuristics, compute_error_pattern,
    get_all_students, compute_composite_score
)
from metrics_utils import (
    compute_bleu_chrf, compute_semantic_score, compute_edits_effort,
    plot_radar_for_student_metrics
)
from ai_utils import add_ai_practices_to_queue  # LLM-based generation

# -----------------------------
# AUTHENTICATION
# -----------------------------
def show_login():
    st.markdown("### 🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if validate_login(username, password):
            st.session_state.username = username
            st.session_state.role = get_user_role(username)
            st.experimental_rerun()
        else:
            st.error("Invalid login")

def show_register():
    st.markdown("### 📝 Register")
    username = st.text_input("Username", key="r_user")
    password = st.text_input("Password", type="password", key="r_pass")
    role = st.selectbox("Role", ["Student", "Instructor", "Admin"])
    if st.button("Register"):
        ok = register_user(username, password, role)
        if ok:
            st.success("Registration successful!")
        else:
            st.error("Username already exists.")

# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------
CATEGORY_COLORS = {"vocabulary":"#ff4d4d","structure":"#ff944d","meaning":"#ffd11a","editing":"#80ff80"}

def get_color_by_score(score):
    if score >= 0.7: return "#ff4d4d"
    elif score >= 0.4: return "#ff944d"
    elif score >= 0.1: return "#ffd11a"
    else: return "#80ff80"

def generate_feedback(bleu,chrf,semantic,effort):
    feedback=[]
    if bleu<0.3: feedback.append("Vocabulary: Use more precise words.")
    if chrf<0.4: feedback.append("Structure: Review sentence construction.")
    if semantic<0.6: feedback.append("Meaning: Preserve semantic nuance.")
    if effort>50: feedback.append("Editing: Reduce number of revisions needed.")
    return feedback

def plot_progress_timeline(username):
    submissions=get_submissions(username)
    if not submissions: return None
    df=pd.DataFrame(submissions)
    df['timestamp']=pd.to_datetime(df['timestamp'])
    df=df.sort_values('timestamp')
    metrics=['bleu','chrf','semantic','edits','effort']
    df_plot=df.melt(id_vars='timestamp',value_vars=metrics,var_name='Metric',value_name='Score')
    fig=px.line(df_plot,x='timestamp',y='Score',color='Metric',markers=True,
                 title=f"Progress Timeline for {username}")
    fig.update_layout(xaxis_title="Date",yaxis_title="Score")
    return fig

# -----------------------------
# STUDENT DASHBOARD
# -----------------------------
def student_dashboard():
    st.sidebar.markdown(f"👤 Logged in as: {st.session_state.username} ({st.session_state.role})")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
    st.title("🎓 Student Dashboard")

    # Translation Tasks
    st.subheader("📌 Translation Tasks")
    tasks=get_tasks()
    if not tasks: st.info("No tasks assigned yet.")
    else:
        for tid,text in tasks:
            st.markdown(f"**Task {tid}:** {text}")
            mt_text=st.text_area("Machine Translation (for comparison)",key=f"mt_{tid}")
            post_edit=st.text_area("Your Translation / Post-edit",key=f"pe_{tid}")
            if st.button(f"Submit Task {tid}"):
                bleu,chrf=compute_bleu_chrf(text,post_edit)
                semantic=compute_semantic_score(text,post_edit)
                edits,effort=compute_edits_effort(mt_text,post_edit)
                feedback=generate_feedback(bleu,chrf,semantic,effort)
                save_submission(st.session_state.username,tid,text,mt_text,post_edit,
                                bleu,chrf,semantic,edits,effort,feedback)
                st.success("Submission saved!")
                if feedback:
                    st.markdown("**💡 Feedback:**")
                    for f in feedback: st.write(f"- {f}")

    # Adaptive Practice Queue
    st.subheader("🗂 My Adaptive Practice Queue")
    add_ai_practices_to_queue(st.session_state.username,num_exercises=3)
    queue=get_student_practice(st.session_state.username)
    scores=compute_composite_score(st.session_state.username)
    if not queue: st.info("No practice items yet.")
    else:
        for sp_id,pid,cat,prompt,ref,status,assigned_at,completed_at in queue:
            cat_score=scores.get(cat,0)
            color=get_color_by_score(cat_score)
            status_label=f"[{status.upper()}]"
            st.markdown(f"<div style='background-color:{color};padding:10px;border-radius:5px;margin-bottom:5px;'>"
                        f"**{status_label} ({cat})** {prompt}</div>",unsafe_allow_html=True)
            if status=="recommended" and st.button(f"Do Practice {sp_id}"):
                st.session_state.active_practice=(sp_id,prompt,ref)
                st.experimental_rerun()
            if status=="completed": st.caption(f"Completed: {completed_at}")

        if "active_practice" in st.session_state and st.session_state.active_practice:
            sp_id,prompt,ref=st.session_state.active_practice
            st.text_area("Practice prompt",prompt,disabled=True)
            ans=st.text_area("Your translation",key=f"prac_{sp_id}")
            if st.button("Submit Practice"):
                bleu,chrf=compute_bleu_chrf(ref,ans)
                semantic=compute_semantic_score(ref,ans)
                edits,effort=compute_edits_effort(prompt,ans)
                feedback=generate_feedback(bleu,chrf,semantic,effort)
                mark_practice_completed(sp_id,ans,st.session_state.username,
                                        bleu,chrf,semantic,edits,effort,feedback)
                st.success("Practice completed!")
                if feedback:
                    st.markdown("**💡 Feedback:**")
                    for f in feedback: st.write(f"- {f}")
                st.session_state.active_practice=None
                st.experimental_rerun()

    # Progress Radar
    st.subheader("📊 Progress Overview")
    pattern=compute_error_pattern(st.session_state.username)
    if pattern:
        st.json(pattern)
        fig=plot_radar_for_student_metrics({
            "BLEU": pattern.get("avg_bleu",0),
            "chrF": pattern.get("avg_chrf",0),
            "Semantic": pattern.get("avg_semantic",0),
            "Effort": min(100,pattern.get("avg_effort",0)),
            "Edits": min(100,pattern.get("avg_edits",0))
        })
        st.plotly_chart(fig,use_container_width=True)

    # Progress Timeline
    st.subheader("📈 Progress Timeline")
    fig_timeline=plot_progress_timeline(st.session_state.username)
    if fig_timeline: st.plotly_chart(fig_timeline,use_container_width=True)
    else: st.info("No submissions yet to plot timeline.")

# -----------------------------
# INSTRUCTOR DASHBOARD
# -----------------------------
def instructor_dashboard():
    st.sidebar.markdown(f"👤 Logged in as: {st.session_state.username} ({st.session_state.role})")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
    st.title("👨‍🏫 Instructor Dashboard")

    students=get_all_students()
    if not students: st.info("No students registered yet.")
    else:
        # Class Overview
        st.subheader("📊 Class Overview")
        overview_data=[{
            "Student":s["username"],
            "BLEU":s.get("avg_bleu",0),
            "chrF":s.get("avg_chrf",0),
            "Semantic":s.get("avg_semantic",0),
            "Edits":s.get("avg_edits",0),
            "Effort":s.get("avg_effort",0),
            "Completed Practices":s.get("completed_practices",0)
        } for s in students]
        st.dataframe(pd.DataFrame(overview_data))

        # Weakness Heatmap
        st.subheader("🔥 Weakness Heatmap")
        heatmap_data=pd.DataFrame([{
            "Student":s["username"],
            "Vocabulary":s.get("vocabulary",0),
            "Structure":s.get("structure",0),
            "Meaning":s.get("meaning",0),
            "Editing":s.get("editing",0)
        } for s in students]).set_index("Student")
        fig,ax=plt.subplots(figsize=(8,len(students)*0.5+2))
        sns.heatmap(heatmap_data,annot=True,cmap="Reds",linewidths=0.5,ax=ax)
        st.pyplot(fig)

        # AI Exercise Assignment
        st.subheader("🤖 Generate AI Exercises")
        if st.button("Generate AI Exercises for All Students"):
            for s in students: add_ai_practices_to_queue(s["username"],num_exercises=3)
            st.success("AI exercises generated and assigned.")

        # Student Drill-Down
        st.subheader("🔍 Student Drill-Down")
        student_choice=st.selectbox("Select a student",[s["username"] for s in students])
        if student_choice:
            student_data=next(s for s in students if s["username"]==student_choice)
            st.json(student_data)
            # Radar chart
            fig=plot_radar_for_student_metrics({
                "BLEU": student_data.get("avg_bleu",0),
                "chrF": student_data.get("avg_chrf",0),
                "Semantic": student_data.get("avg_semantic",0),
                "Effort": student_data.get("avg_effort",0),
                "Edits": student_data.get("avg_edits",0)
            })
            st.plotly_chart(fig,use_container_width=True)
            # Timeline chart
            fig_timeline=plot_progress_timeline(student_choice)
            if fig_timeline: st.plotly_chart(fig_timeline,use_container_width=True)
            else: st.info("No submissions yet for this student.")

# -----------------------------
# MAIN
# -----------------------------
def main():
    init_db()
    if "username" not in st.session_state: st.session_state.username=None
    if st.session_state.username is None:
        tab1,tab2=st.tabs(["Login","Register"])
        with tab1: show_login()
        with tab2: show_register()
    else:
        role=st.session_state.role
        if role=="Student": student_dashboard()
        elif role=="Instructor": instructor_dashboard()
        elif role=="Admin": st.warning("Admin features not implemented yet")

if __name__=="__main__":
    main()
