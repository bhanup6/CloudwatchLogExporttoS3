from flask import Flask, render_template
from utils import initialize_database, get_export_statuses, update_export_status

app = Flask(__name__)

@app.route('/')
def dashboard():
    initialize_database()
    
    # Update all task statuses
    statuses = get_export_statuses()
    for task in statuses:
        update_export_status(task[0])
    
    return render_template('dashboard.html', exports=get_export_statuses())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
