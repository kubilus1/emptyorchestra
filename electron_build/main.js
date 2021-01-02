const {app, BrowserWindow} = require('electron')
const path = require('path')

const PY_DIST_FOLDER = '../dist'
const PY_FOLDER = '..'
const PY_MODULE = 'emptyorch' // without .py suffix


const guessPackaged = () => {
  /*const fullPath = path.join(__dirname, PY_DIST_FOLDER)
  return require('fs').existsSync(fullPath)*/
    if (process.env.DEVMODE == '1') {
        return false
    } else {
        return true
    }
}

const getScriptPath = () => {
    if (process.env.DEVMODE == '1') {
        return path.join(__dirname, '..', 'emptyorch')
        //extraResources/emptyorch_min_amd64_linux
        //return path.join(__dirname, '..', 'extraResources', 'emptyorch_min_amd64_linux')
    } else {
        if (process.platform === 'win32') {
            return path.join(__dirname, '..', 'dist', 'emptyorch_win.exe')
        } else {
            return path.join(__dirname, '..', 'dist', 'emptyorch_min_amd64_linux')
        }
    }
 /*
  if (!guessPackaged()) {
    return path.join(__dirname, PY_FOLDER, PY_MODULE + '.py')
  }
  if (process.platform === 'win32') {
    return path.join(__dirname, PY_DIST_FOLDER, PY_MODULE, PY_MODULE + '.exe')
  }
  return path.join(__dirname, PY_DIST_FOLDER, PY_MODULE, PY_MODULE)
  */
}

let pyProc = null

function createServer() {
    let script = getScriptPath()
    let port = 5000

    if (guessPackaged()) {
        console.log("Using released version")
        pyProc = require('child_process').spawn(script, [port], {
            stdio: "inherit",
            detached: false,
            env: {
                'EO_HEADLESS': '1'
            }
        })
    } else {
        console.log("Dev mode")
        pyProc = require('child_process').spawn('python', [script, port], {
            stdio: "inherit",
            detached: false,
            env: {
                'EO_HEADLESS': '1'
            }
        })
    }

    if (pyProc != null) {
        //console.log(pyProc)
        console.log('child process success on port ' + port)
    }
    /*
    let script = path.join(__dirname, '..', 'emptyorch')
    pyProc = require('child_process').spawn('python', [script, port], {
        stdio: "inherit",
        detached: false
    })*/
    //pyProc = require('child_process').spawn('python', [script, port])
}

function exitServer() {
    pyProc.kill()
    pyProc = null
}


function createMainWindow () {
    window = new BrowserWindow({width: 1024, height: 768})
    window.loadURL('http://127.0.0.1:5000/karaoke')
}
function createControlWindow () {
    window = new BrowserWindow({width: 800, height: 600})
    window.loadURL('http://127.0.0.1:5000/control')
}

function startIt() {
    setTimeout(createMainWindow, 1500);
    setTimeout(createControlWindow, 1700);
}


var rq = require('request-promise');
mainAddr = 'http://127.0.0.1:5000/karaoke';
var startUp = function(){
  rq(mainAddr)
    .then(function(htmlString){
      console.log('server started!');
      createMainWindow();
      createControlWindow();
    })
    .catch(function(err){
      //console.log('waiting for the server start...');
      startUp();
    });
};


app.on('ready', createServer)
app.on('will-quit', exitServer)
app.on('ready', startUp)

app.on('window-all-closed', () => {
    // On macOS it is common for applications and their menu bar
    // to stay active until the user quits explicitly with Cmd + Q
    if (process.platform !== 'darwin') {
      app.quit()
    }
})
