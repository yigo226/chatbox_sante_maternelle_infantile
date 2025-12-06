from flask import Flask,session,redirect,render_template
from routes.femme_routes import femme_bp
from routes.enfant_routes import enfant_bp
from routes.chatbox_routes import chatbox_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = b'\xc2\x92\xdf\xd8\\WU\xb7f\x98\xc6\r\x92\xd9\xb5\x8c'
    #b'\xc2\x92\xdf\xd8\\WU\xb7f\x98\xc6\r\x92\xd9\xb5\x8c'

    # Enregistrement des blueprints
    app.register_blueprint(femme_bp)
    app.register_blueprint(enfant_bp)
    app.register_blueprint(chatbox_bp)
    # Accueil
    
    @app.route("/")
    def home():
        #if "femme" in session:
            return redirect("/index")
        #return render_template("/login.html")
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
