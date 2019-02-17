from flask import Flask, render_template, request

from src.main import main

api = Flask(__name__)


@api.route('/', methods=['GET', 'POST'])
def display_planning():
    planning = ''
    if request.method == 'POST':
        if request.form['submit_button'] == 'Do Plan':
            planning = main()
            for x in planning:
                x['names'] = x['name'].replace('_', ' ')

    return render_template('planning.html', data=planning)


if __name__ == '__main__':
    api.run(host='0.0.0.0', port=5000, debug=True)
