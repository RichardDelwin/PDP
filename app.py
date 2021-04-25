import numpy as np
import os, pandas, sys
from flask import Flask, flash, request, redirect, url_for, session
from flask import send_from_directory, render_template, jsonify
from werkzeug.utils import secure_filename
from functions.datscan_predict import datscan_predict
from functions.datscan_explain import datscan_explain
from functions.db_functions import writeToDB , readFromDB , readSingleFromDB
from speech_diagnosis.src.Audio_Controller import Audio_Controller
import datetime, pytz
from uuid import uuid4



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './files/'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/history')
def history():
    details=readFromDB()
    
    return render_template('history.html',details = details)

@app.route('/results', methods=['GET', 'POST'])
def results():
      id = request.form['id']
      temp=readSingleFromDB(id)
      print(temp)
      return render_template('results.html',temp = temp)

@app.route('/form_upload', methods=['GET', 'POST'])
def form_upload():

    if request.method == "POST":
        first = request.form['FirstName']
        last = request.form['LastName']
        age = request.form['age']
        gender = request.form['gender']

        file_paths = {'datscan': None, 'speech': None}
        file_paths = get_file_path(request=request)
        print("FILE_PATHS",file_paths)


        if file_paths['datscan'] != None:
            hasPDdatscan = datscan_predict(file_paths['datscan'])
        else:
            hasPDdatscan = None
        #datscan_explain(file_paths['datscan'])

        if file_paths.get('speech',None) != None:
            audio = Audio_Controller(file_paths['speech'])
            audio.process_audio()
            hasPDspeech = audio.predict_PD_diagnosis(model_name="RF")
        else:
            hasPDspeech = None

        current_time = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))

        data = {
            'first': first,
            'last': last,
            'age': age,
            'gender': gender,
            'hasPDdatscan': hasPDdatscan,
            'datscanPath': file_paths['datscan'],
            'hasPDspeech': hasPDspeech,
            'speechPath': file_paths['speech'],
            'predictTime': current_time
        }
        print(data)

        writeToDB(data)

        return render_template('datscan_output.html', data=data)

    elif request.method == 'GET':
        scans = os.listdir('files/datscan')
        return render_template('datscan_form.html', scans=scans)


def get_file_path(request):

    file_paths = {"datscan":None, "speech":None}

    for file_type in file_paths.keys():

        if file_type not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files[file_type]

        if file.filename == '':
            flash('No selected file')
            # return redirect(request.url)

        filename = None
        file_path = None

        if file:
            filename = make_unique(secure_filename(file.filename))
            print("FILENAME", filename)
            file.save(os.path.join("../PDP/files/{0}/".format(file_type), filename))
            file_path = os.path.join("../PDP/files/{}".format(file_type), filename)

        file_paths[file_type] = file_path

    return file_paths

#Adds four random characters to the start of the file name
def make_unique(string):
    ident = uuid4().__str__()[:4]  
    return f"{ident}-{string}"


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run(debug = True)
