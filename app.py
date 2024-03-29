from flask import Flask, request, render_template_string
from flask_socketio import SocketIO, emit
from beem import Hive
from beem.account import Account

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/', methods=['GET'])
def index():
    return render_template_string('''
    <!doctype html>
    <html>
        <head>
            <title>Who Downvotes me on Hive?</title>
        <style>
            a {
              color:red;
            text-decoration:none;                    
            }                      
            body {
                    font-family: monospace;
                    color: #039F79;
                    background-color: #0D0D0D;              
                }
                table, th, td {
                    border: 0px solid black;
                    border-collapse: collapse;
                }
                th, td {
                    padding: 5px;
                    text-align: left;
                }
             header {
                background: #333; 
                color: #fff;  
                padding: 10px 0; 
                top:0px;                          
            }
            .container {
                display: flex;
                justify-content: center; 
                align-items: center;
                height: 100vh; 
            }                      
            </style>
        </head>
        <body>
            <div class="container">
            <div>
            <p style="font-size:16px; font-weight: bold;">Who <span style="color: red;">downvotes</span> me on Hive?</p>
            <form action="/result" method="post">
                <label for="username">username:</label>
                <input type="text" id="username" name="username" required>
                <button type="submit">Submit</button>
            </form>
            </div>
            </div>
        </body>
    </html>
    ''')

@app.route('/result', methods=['POST'])
def result():
    username = request.form['username']
    return render_template_string('''
    <!doctype html>
    <html>
        <head>
            <title>Who Downvotes me on Hive?</title>
            <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
            <style>
            a {
              color:red;
            text-decoration:none;                    
            }                      
            body {
                    font-family: monospace;
                    color: #039F79;
                    background-color: #0D0D0D;              
                }
                table, th, td {
                    border: 0px solid black;
                    border-collapse: collapse;
                    
                }
                th, td {
                    padding: 5px;
                    text-align: left;
                }
             header {
                background: #333; 
                color: #fff; 
                text-align: center;
                padding: 10px 0; 
                position: sticky;
                top: 0;
                z-index: 1000;                       
            }
            .container {
                display: flex;
                justify-content: center; 
                align-items: center;
                
            }            

            @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
            }

            .fade-in {
            animation: fadeIn 0.5s; 
            }                         
            </style>
        </head>

        <body>
            <header> 
            <form action="/result" method="post">
                <label for="username">username:</label>
                <input type="text" id="username" name="username" required>
                <button type="submit">Submit</button>
                <input type="text" id="filter" onkeyup="filterTable()" placeholder="Type to filter...">

            </form>                       
            </header> 
            <div class="container"> 
            <div>
            <h2>Downvotes para {{ username }}</h2>
                                
            <table id="downvotesTable">
                <tr>
                    <th>Downvoter</th>
                    <th>Post Link</th>
                    <th>Downvote Power %</th>
                    <th>Date</th>                                  
                </tr>
                               
            </table>
            </div>
            </div>
            
            <script type="text/javascript" charset="utf-8">
                var socket = io.connect('http://' + document.domain + ':' + location.port);
                socket.on('connect', function() {
                    socket.emit('get_downvotes', {username: "{{ username }}"});
                });
                socket.on('downvote_info', function(msg) {
                    var table = document.getElementById("downvotesTable");
                    var row = table.insertRow(-1);
                    row.className = 'fade-in';
                    var cell1 = row.insertCell(0);
                    var cell2 = row.insertCell(1);
                    var cell3 = row.insertCell(2);
                    var cell4 = row.insertCell(3);  // Nueva celda para la fecha del downvote
                    cell1.innerHTML = msg.user;
                    cell2.innerHTML = '<a href="' + msg.link + '" target="_blank">' + msg.link + '</a>';
                    cell3.innerHTML = msg.downvote_percentage.toFixed(2) + '%';
                    cell4.innerHTML = msg.timestamp;  // Mostrar la fecha del downvote
                });
                function filterTable() {
                    var filter, table, tr, td, i, txtValue;
                    filter = document.getElementById("filter").value.toUpperCase();
                    table = document.getElementById("downvotesTable");
                    tr = table.getElementsByTagName("tr");
                    for (i = 1; i < tr.length; i++) {  // Empieza en 1 para saltar la cabecera de la tabla
                        td = tr[i].getElementsByTagName("td")[0];  // Obtiene la celda del downvoter (primera columna)
                        if (td) {
                            txtValue = td.textContent || td.innerText;
                            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                                tr[i].style.display = "";
                            } else {
                                tr[i].style.display = "none";
                            }
                        }       
                    }
                }
                                  
            </script>
        </body>
    </html>
    ''', username=username)

@socketio.on('get_downvotes')
def get_downvotes(message):
    username = message['username']
    hive = Hive()
    account = Account(username, blockchain_instance=hive)

    for operation in account.history(only_ops=["vote"]):
        if operation['type'] == 'vote' and operation['weight'] < 0:
            weight = operation['weight']
            downvote_percentage = abs(weight) / 10000 * 100
            post_url = f"https://peakd.com/@{operation['author']}/{operation['permlink']}"
            timestamp = operation['timestamp']  # Obtener la fecha del downvote
            downvote_info = {
                'user': operation['voter'],
                'link': post_url,
                'downvote_percentage': downvote_percentage,
                'timestamp': str(timestamp)  # Convertir la fecha a string para emitir
            }
            emit('downvote_info', downvote_info)

#if __name__ == '__main__':
#    socketio.run(app, debug=True)
