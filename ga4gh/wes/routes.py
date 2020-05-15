from flask import url_for, jsonify, current_app as app, Blueprint
from ga4gh.wes.tasks import long_task


simple_page = Blueprint('simple_page', __name__)


@simple_page.route('/start_task', methods=['GET', 'POST'])
def longtask():
    task = long_task.apply_async()
    return jsonify({'Location': url_for('simple_page.taskstatus', task_id=task.id)}), 202


@simple_page.route('/status/<task_id>')
def taskstatus(task_id):
    task = long_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)
