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
    
    // 用户集合按钮点击事件
    $('#userCollectionBtn').click(function() {
        loadUserCollection();
        $('#userCollectionModal').modal('show');
    });
    
    // 刷新用户列表按钮点击事件
    $('#refreshUserListBtn').click(function() {
        loadUserCollection();
    });
    
    // 添加用户表单提交事件
    $('#addUserForm').submit(function(e) {
        e.preventDefault();
        addUserToCollection();
    });
});

// 加载用户集合
function loadUserCollection() {
    $.ajax({
        url: '/api/users',
        type: 'GET',
        success: function(response) {
            if (response.status === 'success') {
                renderUserCollection(response.data);
            } else {
                showToast('加载用户集合失败: ' + response.message, 'danger');
            }
        },
        error: function(xhr, status, error) {
            showToast('请求失败: ' + error, 'danger');
        }
    });
}

// 渲染用户集合
function renderUserCollection(users) {
    const $userList = $('#userCollectionList');
    $userList.empty();
    
    if (users.length === 0) {
        $userList.html('<tr><td colspan="3" class="text-center">暂无用户，请添加</td></tr>');
        return;
    }
    
    users.forEach(function(user) {
        const shortLink = user.user_link.length > 40 ? 
            user.user_link.substring(0, 37) + '...' : 
            user.user_link;
            
        const $row = $(`
            <tr data-id="${user.id}">
                <td>${user.custom_name}</td>
                <td><small>${shortLink}</small></td>
                <td>
                    <button class="btn btn-sm btn-primary select-user-btn" data-link="${user.user_link}">
                        <i class="bi bi-cursor-fill"></i> 选择
                    </button>
                    <button class="btn btn-sm btn-danger delete-user-btn">
                        <i class="bi bi-trash"></i> 删除
                    </button>
                </td>
            </tr>
        `);
        
        $userList.append($row);
    });
    
    // 绑定选择用户按钮点击事件
    $('.select-user-btn').click(function() {
        const link = $(this).data('link');
        selectUser(link);
    });
    
    // 绑定删除用户按钮点击事件
    $('.delete-user-btn').click(function() {
        const userId = $(this).closest('tr').data('id');
        deleteUser(userId);
    });
}

// 添加用户到集合
function addUserToCollection() {
    const userLink = $('#userLink').val().trim();
    const customName = $('#customName').val().trim();
    
    if (!userLink) {
        showToast('请输入用户链接', 'warning');
        return;
    }
    
    $.ajax({
        url: '/api/users',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            user_link: userLink,
            custom_name: customName
        }),
        success: function(response) {
            if (response.status === 'success') {
                showToast('用户添加成功', 'success');
                loadUserCollection();
                // 清空表单
                $('#userLink').val('');
                $('#customName').val('');
            } else {
                showToast('添加用户失败: ' + response.message, 'danger');
            }
        },
        error: function(xhr, status, error) {
            showToast('请求失败: ' + error, 'danger');
        }
    });
}

// 删除用户
function deleteUser(userId) {
    if (!confirm('确定要删除此用户吗？')) {
        return;
    }
    
    $.ajax({
        url: '/api/users/' + userId,
        type: 'DELETE',
        success: function(response) {
            if (response.status === 'success') {
                showToast('用户删除成功', 'success');
                loadUserCollection();
            } else {
                showToast('删除用户失败: ' + response.message, 'danger');
            }
        },
        error: function(xhr, status, error) {
            showToast('请求失败: ' + error, 'danger');
        }
    });
}

// 选择用户
function selectUser(link) {
    // 获取当前输入框中的内容
    const currentLinks = $('#links').val();
    
    // 如果当前内容为空，直接设置链接
    if (!currentLinks) {
        $('#links').val(link);
    } else {
        // 检查链接是否已存在
        const linkLines = currentLinks.split('\n');
        if (!linkLines.includes(link)) {
            // 如果链接不存在，则添加到末尾
            $('#links').val(currentLinks + '\n' + link);
        } else {
            showToast('链接已存在', 'info');
        }
    }
    
    // 关闭模态框
    $('#userCollectionModal').modal('hide');
    
    // 显示提示
    showToast('已添加链接到下载列表', 'success');
}

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
                            $('#progressContainer').show();
                            
                            // 清空输出日志
                            $('#outputLog').empty();
                            
                            // 更新按钮状态
                            $('#runBtn').prop('disabled', true).html('<i class="bi bi-hourglass-split me-2"></i>下载中...');
                            
                            // 显示提示
                            showToast('下载任务已启动', 'success');
                        } else {
                            // 恢复按钮状态
                            $('#runBtn').prop('disabled', false).html('<i class="bi bi-cloud-download me-2"></i>开始下载');
                            
                            // 显示错误提示
                            showToast('启动下载任务失败: ' + runResponse.message, 'danger');
                        }
                    },
                    error: function(xhr, status, error) {
                        // 恢复按钮状态
                        $('#runBtn').prop('disabled', false).html('<i class="bi bi-cloud-download me-2"></i>开始下载');
                        
                        // 显示错误提示
                        showToast('请求失败: ' + error, 'danger');
                    }
                });
            } else {
                // 恢复按钮状态
                $('#runBtn').prop('disabled', false).html('<i class="bi bi-cloud-download me-2"></i>开始下载');
                
                // 显示错误提示
                showToast('保存配置失败: ' + response.message, 'danger');
            }
        },
        error: function(xhr, status, error) {
            // 恢复按钮状态
            $('#runBtn').prop('disabled', false).html('<i class="bi bi-cloud-download me-2"></i>开始下载');
            
            // 显示错误提示
            showToast('请求失败: ' + error, 'danger');
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
            
            // 显示结果提示
            if (response.status === 'success') {
                showToast('下载任务已停止', 'success');
                resetDownloadUI();
            } else if (response.status === 'warning') {
                showToast(response.message, 'warning');
            } else {
                showToast('停止下载任务失败: ' + response.message, 'danger');
            }
        },
        error: function(xhr, status, error) {
            // 恢复按钮状态
            $('#stopBtn').prop('disabled', false).html('<i class="bi bi-stop-fill me-1"></i>停止下载');
            
            // 显示错误提示
            showToast('请求失败: ' + error, 'danger');
        }
    });
}

// 重置下载UI
function resetDownloadUI() {
    isDownloading = false;
    
    // 恢复按钮状态
    $('#runBtn').prop('disabled', false).html('<i class="bi bi-cloud-download me-2"></i>开始下载');
    $('#stopBtn').prop('disabled', false).html('<i class="bi bi-stop-fill me-1"></i>停止下载');
    
    // 重置进度条
    $('#progressBar').css('width', '0%').attr('aria-valuenow', 0).text('0%');
}

// 显示提示框
function showToast(message, type = 'success') {
    const toastId = 'toast-' + Date.now();
    
    // 创建提示框元素
    const toast = `
        <div id="${toastId}" class="toast bg-${type}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="me-auto">${type === 'success' ? '成功' : type === 'warning' ? '警告' : type === 'danger' ? '错误' : '提示'}</strong>
                <small>${new Date().toLocaleTimeString()}</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body text-white">
                ${message}
            </div>
        </div>
    `;
    
    // 添加到容器
    $('#toast-container').append(toast);
    
    // 初始化提示框
    const toastElement = new bootstrap.Toast(document.getElementById(toastId), {
        delay: 3000
    });
    
    // 显示提示框
    toastElement.show();
    
    // 提示框关闭后删除元素
    $(`#${toastId}`).on('hidden.bs.toast', function() {
        $(this).remove();
    });
} 