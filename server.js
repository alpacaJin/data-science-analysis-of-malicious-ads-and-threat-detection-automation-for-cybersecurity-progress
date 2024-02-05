// const WebSocket = require('ws');
// const fs = require('fs');
// const filePath = 'static/company_locality.csv';

// const wss = new WebSocket.Server({ port: 8080 });

// wss.on('connection', function connection(ws) {
//     console.log('Client connected');
    
//     // Function to send newly added line to all connected clients
//     const sendNewLine = (line) => {
//         wss.clients.forEach(function each(client) {
//             if (client.readyState === WebSocket.OPEN) {
//                 client.send(line);
//             }
//         });
//     };

//     // Watch the CSV file for changes
//     fs.watchFile(filePath, (curr, prev) => {
//         if (curr.mtime > prev.mtime) {
//             fs.readFile(filePath, 'utf8', (err, data) => {
//                 if (err) {
//                     console.error('Error reading file:', err);
//                     return;
//                 }
//                 // Send only the last line assuming it's the newly added one
//                 const lines = data.trim().split('\n');
//                 const lastLine = lines[lines.length - 1];
//                 sendNewLine(lastLine);
//             });
//         }
//     });
// });

const express = require('express');
const fs = require('fs');
const Papa = require('papaparse');
const app = express();
const port = 3000;

// Serve static files from public directory
app.use(express.static('public'));

// API endpoint for CSV data
app.get('/data', (req, res) => {
    fs.readFile('static/company_locality.csv', 'utf8', (err, data) => {
        if (err) {
            console.error("Error reading file:", err);
            res.status(500).send("Error reading CSV file");
            return;
        }
        const result = Papa.parse(data, {
            header: true,
            dynamicTyping: true,
        });
        res.json(result.data);
    });
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});