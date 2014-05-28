var guid = (function() {
  function s4() {
    return Math.floor((1 + Math.random()) * 0x10000)
               .toString(16)
               .substring(1);
  }
  return function() {
    return s4() + s4() + '-' + s4() + '-' + s4() + '-' +
           s4() + '-' + s4() + s4() + s4();
  };
})();

function desktopNotification(title,text,icon) {
    var notification = new Notification(title, {
        body: text,
        icon: icon
    });
    notification.onclick = function() {
        try {
            window.blur();
            setTimeout(window.focus, 0);
            notification.close();
        } catch(e) {}
    };
    setTimeout(function(){
        try {
            notification.close();
        } catch(e) {}
    },5000);
    window.onbeforeunload = function(){
        try {
            notification.close();
        } catch(e) {}
    };
    window.addEventListener("focus", function(event) {
        try {
            notification.close();
        } catch(e) {}
    }, false);
}