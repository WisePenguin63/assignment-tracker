# Addapted from CS50's Finance PS

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from email_validator import validate_email
from datetime import datetime

from helpers import apology, login_required, logged_in, now, datetime_convert

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///planner.db")

COLOURS = ["default", "primary", "secondary", "success",
           "danger", "warning", "info", "light", "dark"]
PRIORITY = [["Low", "Normal", "High"], ["success", "warning", "danger"]]

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    if logged_in():
        return redirect("/home")
    return render_template("index.html")


@app.route("/home")
@login_required
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    # If login submitted
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        users = db.execute(
            """
            SELECT *
            FROM users
            WHERE email = :email
            """,
            email=email)

        if len(users) != 1 or not check_password_hash(users[0]["password_hash"], password):
            return apology("Username and/or Password incorrect")
        app.logger.info("Login Succesfull")
        session["user_id"] = users[0]["id"]
        return redirect('/home')

    # Login form
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():

    # Register form submitted
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        password2 = request.form.get("password2")
        if not (email and password and password2):
            return render_template("register.html", error="Complete every box")
        if password != password2:
            return render_template("register.html", error="Passwords must match")
        if (db.execute(
            """
            SELECT *
            FROM users
            WHERE email = :email
            """,
            email=email
        )):
            return render_template("register.html", error="Email already registerd")
        try:
            validate_email(email)
        except:
            return render_template("register.html", error="Invalid email")
        hash = generate_password_hash(password)
        e = db.execute(
            """
            INSERT INTO users (email, password_hash)
            VALUES (:email, :password)
            """,
            email=email, password=hash
        )
        if not e:
            return apology("error")
        q = db.execute(
            """
            INSERT INTO courses (user_id, name, details)
            VALUES (:user, :name, :details)
            """,
            user=e,
            name="Default",
            details="This is the default course"
        )
        return redirect("/login")

    # Registration form
    else:
        return render_template("register.html")


@app.route("/courses", methods=["GET", "POST"])
@login_required
def courses():

    # Course form submitted
    if request.method == "POST":
        # Get submited values
        name = request.form.get("name")
        desc = request.form.get("desc")
        colour = request.form.get("colour")
        id = request.form.get("id")

        # Deleting Course
        if request.form.get("submit_button") == "delete_button":
            deleted = db.execute(
                """
                DELETE
                FROM courses
                WHERE id=:id
                AND user_id=:user
                """,
                id=id,
                user=session["user_id"]
            )
            app.logger.info("deleted course: ", deleted)
            if deleted == 0:
                return apology("Deleting failed - No courses with that ID")
            if deleted > 1:
                return apology("It seems several things have that ID. Check to make sure you still have all your courses")

        elif request.form.get("submit_button") == "submit_button":
            # Editing Course
            if id is not None:
                course = db.execute(
                    """
                    SELECT *
                    FROM courses
                    WHERE id=:id
                    AND user_id=:user
                    """,
                    id=id,
                    user=session["user_id"]
                )[0]

                # ID for course editing doesnt exist
                if course is None:
                    return apology("It seems you've tried to edit a non-existant course")

                if course["user_id"] != session["user_id"]:
                    return apology("It seems you've tried to edit a non-existant course")

                # Insert into database
                updated_rows = db.execute(
                    """
                    UPDATE courses
                    SET name=:name,
                    details=:desc,
                    colour=:colour
                    WHERE id=:id
                    AND user_id=:user
                    """,
                    name=name,
                    desc=desc,
                    colour=colour,
                    id=id,
                    user=session["user_id"]
                )
                if updated_rows == 0:
                    return apology("An error seems to have occured")
                elif updated_rows > 1:
                    return apology("You seem to have broken the system")

            # Creating Course
            else:
                # Insert into database
                if db.execute(
                    """
                    INSERT INTO courses
                    (user_id, name, details, colour)
                    VALUES (:user, :name, :desc, :colour)
                    """,
                    user=session["user_id"],
                    name=name,
                    desc=desc,
                    colour=colour
                ):
                    app.logger.info("Course insertion successfull")
                else:
                    app.logger.info("Course insertion error")

        else:
            return apology("That button id is wrong")

        # Load courses page
        return redirect("/courses")

    # Default page
    else:
        courses_ar = db.execute(
            """
            SELECT *
            FROM courses
            WHERE user_id = :user
            """,
            user=session["user_id"]
        )
        return render_template("courses.html", courses=courses_ar)


@app.route("/add_course", methods=["GET", "POST"])
@login_required
def add_course():
    # Editing course
    if request.method == "POST":
        id = request.form.get("id")
        course = db.execute(
            """
            SELECT *
            FROM courses
            WHERE id = :id
            AND user_id = :user
            """,
            id=id,
            user=session["user_id"]
        )[0]
        if course is None:
            return apology("Course not found")
        return render_template("add_course.html", change="Edit", course=course, colours=COLOURS)
    return render_template("add_course.html", change="Add", colours=COLOURS)


@app.route("/assignments", methods=["GET", "POST"])
@login_required
def assignments():
    # View
    if request.method == "GET":
        id = request.args.get("id")
        # View all assignments
        if not id:

            courses = db.execute(
                """
                SELECT name, id
                FROM courses
                WHERE user_id = :user
                """,
                user=session["user_id"]
            )

            query = """
                SELECT assignments.id,
                    assignments.title,
                    assignments.due_date,
                    assignments.completion_status,
                    assignments.priority,
                    courses.name,
                    courses.colour
                FROM assignments
                JOIN courses ON assignments.course_id = courses.id
                WHERE assignments.user_id = :user
                """

            params = {
                "user": session["user_id"]
            }

            conditions = []

            complete = request.args.get("filter-completion", "0")
            if complete == "2":
                conditions.append("assignments.completion_status IN (:completion0, :completion1)")
                params["completion0"] = 0
                params["completion1"] = 1
            else:
                conditions.append("assignments.completion_status = :completion")
                params["completion"] = int(complete)

            course = request.args.get("filter-course", "All courses")
            if course != "All courses":
                conditions.append("assignments.course_id = :course")
                params["course"] = course

            search = request.args.get("search-assignment", "")
            if search:
                conditions.append("assignments.title LIKE :search")
                params["search"] = "%" + search + "%"

            priority = request.args.get("filter-priority", "0")
            if priority != '0':
                conditions.append("assignments.priority = :priority")
                params["priority"] = priority

            if conditions:
                query += " AND " + " AND ".join(conditions)

            sort = request.args.get("sort-assignments", "Due first")
            if "first" in sort:
                asdes = "ASC"
            else:
                asdes = "DESC"
            if "Due" in sort:
                sort = "due_date IS NULL, due_date"
            else:
                sort = "title"
            query += f" ORDER BY assignments.{sort} {asdes}"

            assignments_arr = db.execute(query, **params)

            filters = request.args

            for assignment in assignments_arr:
                if assignment["due_date"]:
                    if assignment["due_date"] < now() and assignment["due_date"] != "" and assignment["completion_status"] == 0:
                        assignment["colour"] = "danger"
                    assignment["due_date"] = datetime_convert(assignment["due_date"])
                assignment["priority-c"] = PRIORITY[1][assignment["priority"]-1]
                assignment["priority"] = PRIORITY[0][assignment["priority"]-1]
            return render_template("assignments.html", assignments=assignments_arr, courses=courses, filters=filters)

        # View assignment details
        else:
            try:
                if db.execute(
                    """
                    SELECT user_id
                    FROM assignments
                    WHERE id=:id
                    """,
                    id=id
                )[0]["user_id"] == session["user_id"]:
                    app.logger.info("Their assignment")

                # Not their assignment
                else:
                    app.logger.info("not their assignment")
                    return apology("Assignment doesn't exist", 404)

            # Assignment doesn't exist
            except IndexError:
                app.logger.info("Assignment doesn't exist")
                return apology("Assignment doesn't exist", 404)

            # Their assignment

            # Check completion change
            complete = request.args.get("complete")
            if complete == "True":
                complete = 1
            elif complete == "False":
                complete = 0
            else:
                complete = None
            if complete is not None:
                db.execute(
                    """
                    UPDATE assignments
                    SET completion_status=:status
                    WHERE id=:id
                    AND user_id=:user
                    """,
                    id=id,
                    status=complete,
                    user=session["user_id"]
                )

            # Delete assignment
            if request.args.get("submit_button") == "delete_button":
                deleted = db.execute(
                    """
                    DELETE
                    FROM assignments
                    WHERE id=:id
                    AND user_id=:user
                    """,
                    id=id,
                    user=session["user_id"]
                )
                app.logger.info("deleted assignment: ", deleted)
                if deleted == 0:
                    return apology("Deleting failed - No courses with that ID")
                if deleted > 1:
                    return apology("It seems several things have that ID. Check to make sure you still have all your courses")
                return redirect("/assignments?")



            # View assignment
            assignment = db.execute(
                """
                SELECT assignments.*, courses.name, courses.colour
                FROM assignments
                JOIN courses ON assignments.course_id = courses.id
                WHERE assignments.id = :id
                AND assignments.user_id=:user
                """,
                id=id,
                user=session["user_id"]
            )[0]
            if assignment["due_date"]:
                assignment["due_date"] = datetime_convert(assignment["due_date"])
            assignment["priority"] = PRIORITY[0][assignment["priority"]-1]

            tasks = db.execute(
                """
                SELECT id, title, completion_status
                FROM tasks
                WHERE assignment_id == :assignment
                """,
                assignment=id
            )

            app.logger.debug(f"tasks = {tasks}")
            return render_template("assignment.html", assignment=assignment, tasks=tasks)

    # Add/edit
    else:
        id = request.form.get("id")
        # Canceled
        if request.form.get("submit_button") == "Cancel":
            if id:
                return redirect(f"/assignments?id={id}")
            return redirect("/assignments?")

        # Submited
        else:
            # Get submitted values
            name = request.form.get("name")
            course = request.form.get("course")
            desc = request.form.get("desc")
            due_date = request.form.get("due_date")
            if not due_date:
                due_date = None
            else:
                due_date = datetime.strptime(due_date, '%Y-%m-%dT%H:%M')
            completion_status = request.form.get("completion_status")
            priority = request.form.get("priority")

            try:
                if db.execute(
                    """
                    SELECT user_id
                    FROM courses
                    WHERE id=:id
                    """,
                    id=course
                )[0]["user_id"] == session["user_id"]:

                    # If editing
                    if id:

                        # If theirs
                        try:
                            if db.execute(
                                """
                                SELECT user_id
                                FROM assignments
                                WHERE id=:id
                                """,
                                id=id
                            )[0]["user_id"] == session["user_id"]:

                                # Update db
                                updated_rows = db.execute(
                                    """
                                    UPDATE assignments
                                    SET title = :name,
                                    details = :desc,
                                    due_date = :due,
                                    completion_status = :completion_status,
                                    priority = :priority
                                    WHERE id = :id
                                    AND user_id = :user
                                    """,
                                    name=name,
                                    desc=desc,
                                    due=due_date,
                                    completion_status=completion_status,
                                    id=id,
                                    user=session["user_id"],
                                    priority=priority
                                )

                                if updated_rows != 1:
                                    return apology("An error seems to have occured. Check all of your stuff.", 418)

                            else:
                                return apology("You tried to edit a non-existant assignment", 404)
                        except IndexError:
                            return apology("You tried to edit a non-existant assignment", 404)

                    # If creating
                    else:
                        id = db.execute(
                            """
                            INSERT INTO assignments
                            (user_id, course_id, title, details, due_date, priority)
                            VALUES (:user_id, :course_id, :name, :details, :due_date, :priority)
                            """,
                            user_id=session["user_id"],
                            course_id=int(course),
                            name=name,
                            details=desc,
                            due_date=due_date,
                            priority=priority
                        )

                        if not id:
                            return apology("there has been an error", 500)
                else:
                    return apology("Non-existant course", 404)

            except IndexError:
                return apology("Non-existant course", 404)

        return redirect(f"/assignments?id={id}")

@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    app.logger.debug("Tasks submitted")
    if request.method == "GET":
        return redirect("/assignments")
    else:
        app.logger.debug("Tasks posted")
        id = request.form.get("id")
        user = db.execute(
            """
            SELECT user_id
            FROM assignments
            WHERE id=:id
            """,
            id=id
        )[0]["user_id"]
        if (not id) or user != session["user_id"]:
            app.logger.debug(f"user = {user}, user_id = {session['user_id']}")
            return redirect("/assignments")

        app.logger.debug("Tasks correctly posted")
        # Add Subtask
        if request.form.get("add_subtask") == "true":
            app.logger.debug("Adding Subtask")
            db.execute(
                """
                INSERT INTO tasks (assignment_id, title)
                VALUES (:id, :title)
                """,
                id=id,
                title=request.form.get("subtask_to_add")
            )

        # Update Subtasks
        if request.form.get("update_subtasks") == "true":
            app.logger.debug("Updating subtask")
            submitted=request.form.getlist("subtask")
            subtasks = db.execute(
                """
                SELECT id
                FROM tasks
                WHERE assignment_id = :id
                """,
                id=id
            )

            for subtask in subtasks:
                if str(subtask["id"]) in submitted:
                    comp = 1
                else:
                    comp = 0

                db.execute(
                    """
                    UPDATE tasks
                    SET completion_status = :comp
                    WHERE id = :id
                    """,
                    comp=comp,
                    id=subtask["id"]
                )

        # Delete subtask
        if request.form.get("delete_subtask"):
            app.logger.debug("Deleting Subtasks")
            db.execute(
                """
                DELETE
                FROM tasks
                WHERE id = :task_id
                AND assignment_id = :ass_id
                """,
                task_id=request.form.get("delete_subtask"),
                ass_id=id
            )

        app.logger.debug("redirect assignments")
        return redirect(f"/assignments?id={id}")

@app.route("/add_assignment", methods=["GET", "POST"])
@login_required
def add_assignment():
    courses = db.execute(
        """
        SELECT *
        FROM courses
        WHERE user_id=:id
        """,
        id=session["user_id"]
    )
    if request.method == "POST":
        id = request.form.get("id")
        try:
            if db.execute(
                """
                SELECT user_id
                FROM assignments
                WHERE id=:id
                """,
                id=id
            )[0]["user_id"] == session["user_id"]:
                app.logger.info("Their assignment")

            # Not their assignment
            else:
                app.logger.info("not their assignment")
                return apology("Assignment doesn't exist", 404)

        # Assignment doesn't exist
        except IndexError:
            app.logger.info("Assignment doesn't exist")
            return apology("Assignment doesn't exist", 404)

        assignment = db.execute(
            """
            SELECT assignments.*, courses.name
            FROM assignments
            JOIN courses ON assignments.course_id = courses.id
            WHERE assignments.id = :id
            AND assignments.user_id=:user
            """,
            id=id,
            user=session["user_id"]
        )[0]
        return render_template("add_assignment.html", change="Edit", assignment=assignment, courses=courses)

    else:
        return render_template("add_assignment.html", change="Add", courses=courses)


@app.errorhandler(404)
def not_found(e):
    return apology("This route does not currently exist.~nHowever, it may in the future. ~n:crossed_fingers:", 404)
