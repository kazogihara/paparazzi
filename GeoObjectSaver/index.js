const express = require('express');
const path = require('path');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3').verbose();

const app = express();

let db = new sqlite3.Database('./database.db');
db.serialize(() => {
    db.run("CREATE TABLE IF NOT EXISTS objects (id INTEGER PRIMARY KEY, latitude REAL, longitude REAL, altitude REAL, name TEXT)");
});

app.use(express.static(path.join(__dirname, 'public')));
app.use(bodyParser.json());

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/api/objects', (req, res) => {
    db.all("SELECT * FROM objects", [], (err, rows) => {
        if (err) {
            return res.status(500).json({ error: err.message });
        }
        res.json(rows);
    });
});

app.post('/api/objects', (req, res) => {
    const { latitude, longitude, altitude, name } = req.body;
    if (latitude == null || longitude == null || altitude == null || name == null) {
        return res.status(400).send('Missing required parameters');
    }

    const stmt = db.prepare("INSERT INTO objects (latitude, longitude, altitude, name) VALUES (?, ?, ?, ?)");
    stmt.run(latitude, longitude, altitude, name, function(err) {
        if (err) {
            return res.status(500).send(err.message);
        }
        res.status(201).send({ id: this.lastID });
    });
    stmt.finalize();
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server is running on port ${PORT}`));
