from flask import Flask
from flask_cors import CORS

from services.data_loader import load_data
from services.training import build_or_load_results
from routes import health, recommendations

app = Flask(__name__)
CORS(app)

# load & build results
data = load_data()
all_results = build_or_load_results(data)

# init routes
recommendations.init_routes(all_results)
app.register_blueprint(health.bp)
app.register_blueprint(recommendations.bp)

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="127.0.0.1")



