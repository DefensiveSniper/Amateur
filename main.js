const { app, BrowserWindow, ipcMain, Menu } = require('electron'); 
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');

let flaskProcess;
let win;

// 创建窗口
function createWindow() {
  win = new BrowserWindow({
    width: 1200,
    height: 700,
    icon: path.join(__dirname, 'static', 'images', 'logo.ico'),
    resizable: false,  // 禁止窗口拉伸或缩放
    webPreferences: {
      nodeIntegration: true,  // 允许渲染进程使用 Node.js
    }
  });

  // 检测 Flask 服务是否就绪，若就绪就加载其页面
  const checkServer = () => {
    fetch('http://127.0.0.1:6969')
      .then(() => win.loadURL('http://127.0.0.1:6969'))
      .catch(() => setTimeout(checkServer, 1000));
  };

  checkServer();
}

//  打包时使用
// app.whenReady().then(() => {
//     Menu.setApplicationMenu(null); 
    
//     let flaskPath;
//     if (process.env.NODE_ENV === "development") {
//         flaskPath = path.join(__dirname, 'flask_server.exe'); 
//     } else {
//         flaskPath = path.join(process.resourcesPath, '..', 'flask_server.exe'); 
//     }

//     flaskProcess = spawn(flaskPath, { stdio: 'ignore' });

//     createWindow();

//     app.on('activate', function () {
//       if (BrowserWindow.getAllWindows().length === 0) createWindow();
//     });
// });

//  本地调试时使用,flask_server.py
app.whenReady().then(() => {
    Menu.setApplicationMenu(null); 
    flaskProcess = spawn('python', [path.join(__dirname, 'flask_server.py')]);

    createWindow();

    app.on('activate', function () {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

// 确保 Flask 在 Electron 退出时被关闭
app.on('window-all-closed', function () {
  if (flaskProcess) {
    flaskProcess.kill('SIGTERM');
  }
  app.quit();
});
