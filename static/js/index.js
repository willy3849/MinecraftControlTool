function showAddServerInstructions() {
    Swal.fire({
        icon: 'info',
        title: '如何添加伺服器？',
        html: `
            將你的伺服器丟進 <strong>「~/MinecraftControlTool/servers」</strong><br>
            並重新整理頁面即可！
        `,
        confirmButtonText: '我知道了！'
    });
}