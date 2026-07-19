from flask import Flask

app = Flask(__name__)


@app.route("/")
@app.route("/home")
def main_page():
    return "<h1>Main landing page</h1>"


@app.route("/post")
@app.route("/posts")
@app.route("/articles")
@app.route("/blogs")
def about_page():
    return "<h1>All blogs end up here</h1>"


if __name__ == "__main__":
    app.run(debug=True)

