// 全局变量
let socket;
let isDownloading = false;

// 页面加载完成后执行
$(document).ready(function() {
    // 初始化WebSocket连接
    initSocketIO();
    
    // 保存配置按钮点击事件
    $('#saveBtn').click(function() {
        saveConfig();
    });

    // 开始下载按钮点击事件
    $('#runBtn').click(function() {
        if (isDownloading) {
            showToast('下载任务正在进行中，请等待完成或停止当前任务', 'warning');
            return;
        }
        runDownload();
    });
    
    // 停止下载按钮点击事件
    $('#stopBtn').click(function() {
        stopDownload();
    });
    
    // 清空日志按钮点击事件
    $('#clearLogBtn').click(function() {
        $('#outputLog').empty();
    });
});

// 初始化SocketIO连接
function initSocketIO() {
    // 获取当前URL的主机部分
    const host = window.location.host;
    
    // 创建Socket.IO连接
    socket = io();
    
    // 连接成功事件
    socket.on('connect', function() {
        console.log('已连接到服务器');
    });
    
    // 连接断开事件
    socket.on('disconnect', function() {
        console.log('与服务器的连接已断开');
        if (isDownloading) {
            showToast('下载服务连接已断开', 'danger');
            resetDownloadUI();
        }
    });
    
    // 接收普通输出
    socket.on('output', function(data) {
        appendToLog(data.text);
    });
    
    // 接收进度更新
    socket.on('progress_update', function(data) {
        updateProgress(data.progress);
        appendToLog(data.text);
    });
    
    // 接收错误信息
    socket.on('error', function(data) {
        appendToLog('错误: ' + data.text, 'error');
        showToast('下载过程中发生错误: ' + data.text, 'danger');
    });
    
    // 接收下载完成事件
    socket.on('download_complete', function(data) {
        appendToLog('下载任务已完成', 'success');
        showToast('下载任务已完成', 'success');
        resetDownloadUI();
    });
}

// 更新进度条
function updateProgress(progress) {
    $('#progressBar').css('width', progress + '%').attr('aria-valuenow', progress).text(progress + '%');
    
    // 修改进度条颜色
    const progressBar = $('#progressBar');
    progressBar.removeClass('bg-success bg-info bg-warning bg-danger');
    
    if (progress < 25) {
        progressBar.addClass('bg-danger');
    } else if (progress < 50) {
        progressBar.addClass('bg-warning');
    } else if (progress < 75) {
        progressBar.addClass('bg-info');
    } else {
        progressBar.addClass('bg-success');
    }
}

// 添加日志
function appendToLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    let cssClass = '';
    
    switch (type) {
        case 'error':
            cssClass = 'text-danger';
            break;
        case 'warning':
            cssClass = 'text-warning';
            break;
        case 'success':
            cssClass = 'text-success';
            break;
        default:
            cssClass = '';
    }
    
    const logEntry = $('<div>').addClass(cssClass).html(`[${timestamp}] ${message}`);
    $('#outputLog').append(logEntry);
    
    // 滚动到底部
    const outputLog = document.getElementById('outputLog');
    outputLog.scrollTop = outputLog.scrollHeight;
}

// 保存配置
function saveConfig() {
    // 显示加载状态
    $('#saveBtn').prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 保存中...');
    
    // 收集表单数据
    var formData = new FormData(document.getElementById('configForm'));
    
    // 处理复选框模式（如果没有选中，添加默认值）
    if (!$('input[name="modes"]:checked').length) {
        formData.append('modes', 'post');
    }
    
    // 发送保存请求
    $.ajax({
        url: '/save',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            // 恢复按钮状态
            $('#saveBtn').prop('disabled', false).html('<i class="bi bi-save me-2"></i>保存配置');
            
            // 显示结果提示
            if (response.status === 'success') {
                showToast('配置保存成功', 'success');
            } else {
                showToast('配置保存失败: ' + response.message, 'danger');
            }
        },
        error: function(xhr, status, error) {
            // 恢复按钮状态
            $('#saveBtn').prop('disabled', false).html('<i class="bi bi-save me-2"></i>保存配置');
            
            // 显示错误提示
            showToast('保存请求失败: ' + error, 'danger');
        }
    });
}

// 运行下载任务
function runDownload() {
    // 先保存配置
    var formData = new FormData(document.getElementById('configForm'));
    
    // 处理复选框模式（如果没有选中，添加默认值）
    if (!$('input[name="modes"]:checked').length) {
        formData.append('modes', 'post');
    }
    
    // 显示加载状态
    $('#runBtn').prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 启动中...');
    
    // 先保存配置，再运行下载
    $.ajax({
        url: '/save',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.status === 'success') {
                // 配置保存成功，开始下载
                $.ajax({
                    url: '/run',
                    type: 'POST',
                    success: function(runResponse) {
                        if (runResponse.status === 'success') {
                            // 设置下载状态
                            isDownloading = true;
                            
                            // 显示进度容器
                            $('#progressContainer').slideDown();
                            
                            // 滚动到进度区域
                            $('html, body').animate({
                                scrollTop: $('#progressContainer').offset().top - 20
                            }, 500);
                            
                            // 更新按钮状态
                            $('#runBtn').prop('disabled', true).html('<i class="bi bi-hourglass-split me-2"></i>下载中...');
                            
                            // 清空日志并添加开始信息
                            $('#outputLog').empty();
                            appendToLog('下载任务已启动，正在等待数据...', 'success');
                            
                            // 重置进度条
                            updateProgress(0);
                            
                            // 显示结果提示
                            showToast('下载任务已启动', 'success');
                        } else {
                            // 下载失败
                            $('#runBtn').prop('disabled', false).html('<i class="bi bi-play-fill me-2"></i>开始下载');
                            showToast('下载任务启动失败: ' + runResponse.message, 'danger');
                        }
                    },
                    error: function(xhr, status, error) {
                        // 恢复按钮状态
                        $('#runBtn').prop('disabled', false).html('<i class="bi bi-play-fill me-2"></i>开始下载');
                        
                        // 显示错误提示
                        showToast('下载请求失败: ' + error, 'danger');
                    }
                });
            } else {
                // 配置保存失败
                $('#runBtn').prop('disabled', false).html('<i class="bi bi-play-fill me-2"></i>开始下载');
                showToast('配置保存失败，无法开始下载: ' + response.message, 'danger');
            }
        },
        error: function(xhr, status, error) {
            // 恢复按钮状态
            $('#runBtn').prop('disabled', false).html('<i class="bi bi-play-fill me-2"></i>开始下载');
            
            // 显示错误提示
            showToast('保存配置失败，无法开始下载: ' + error, 'danger');
        }
    });
}

// 停止下载任务
function stopDownload() {
    // 显示加载状态
    $('#stopBtn').prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 停止中...');
    
    // 发送停止请求
    $.ajax({
        url: '/stop',
        type: 'POST',
        success: function(response) {
            // 恢复按钮状态
            $('#stopBtn').prop('disabled', false).html('<i class="bi bi-stop-fill me-1"></i>停止下载');
            
            if (response.status === 'success') {
                resetDownloadUI();
                appendToLog('下载任务已手动停止', 'warning');
                showToast('下载任务已停止', 'warning');
            } else {
                showToast(response.message, response.status === 'warning' ? 'warning' : 'danger');
            }
        },
        error: function(xhr, status, error) {
            // 恢复按钮状态
            $('#stopBtn').prop('disabled', false).html('<i class="bi bi-stop-fill me-1"></i>停止下载');
            
            // 显示错误提示
            showToast('停止请求失败: ' + error, 'danger');
        }
    });
}

// 重置下载UI状态
function resetDownloadUI() {
    isDownloading = false;
    $('#runBtn').prop('disabled', false).html('<i class="bi bi-play-fill me-2"></i>开始下载');
}

// 显示提示框
function showToast(message, type) {
    // 创建随机ID
    var toastId = 'toast-' + Math.floor(Math.random() * 1000000);
    
    // 创建提示框HTML
    var toast = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    // 添加到容器
    $('#toast-container').append(toast);
    
    // 初始化并显示
    var toastElement = document.getElementById(toastId);
    var toastInstance = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 3000
    });
    toastInstance.show();
    
    // 移除监听
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
} 