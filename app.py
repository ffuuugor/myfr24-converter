from flask import Flask, render_template, request, send_file
import os
import tempfile
from converter import read_assets, read_flight_data, convert, remove_duplicates

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('index.html', error='No file part')

        file = request.files['file']

        if file.filename == '':
            return render_template('index.html', error='No selected file')

        if file:
            temp = tempfile.NamedTemporaryFile(delete=False)
            file.save(temp.name)

            airlines_df, planes_df = read_assets('data')
            flights_df = read_flight_data(temp.name)
            df = convert(flights_df, airlines_df, planes_df)
            if request.form.get('remove_duplicates'):
                df = remove_duplicates(df)

            result_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
            df.sort_values(by='Date').to_csv(result_file.name, index=False)
            os.unlink(temp.name)

            return send_file(result_file.name, as_attachment=True, download_name='converted_flights.csv')

    return render_template('index.html')


if __name__ == '__main__':
    app.run()
