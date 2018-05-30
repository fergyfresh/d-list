from deelist import app, db
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4000))
    db.create_all()
    app.run(host="0.0.0.0", port=port, debug=True)
