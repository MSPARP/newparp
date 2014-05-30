var quotes = [
    'Oh god how did this get here I am not good with computer.',
    'Hello everybody! I hope you have a good day!',
    'uggghhhh..... What\'s with all this /green/???',
    'Green is my favorite color 0.0',
    'Hm.... I wonder where all my friends are...',
    'Chara just wished that I have a good time!',
    'Dang! It didn\'t work!',
    'Just little old me~',
    'I wonder what happened...',
    'I hope Charat works today!',
];

jQuery.fn.exists = function(){return this.length>0;}

function cmobile() {
    if (navigator.userAgent.indexOf('Android')!=-1 || navigator.userAgent.indexOf('iPhone')!=-1 || navigator.userAgent.indexOf('Nintendo 3DS')!=-1 || navigator.userAgent.indexOf('Nintendo DSi')!=-1 || window.innerWidth<=630) {
        return true;
    } else {
        return false;
    }
}

function screenCheck() {
    if (cmobile()){
        $(document.body).addClass('mobile');
        $(document.body).removeClass('nobile');
    } else if (window.innerWidth<=950){
        $(document.body).addClass('nobile');
        $(document.body).removeClass('mobile');
    } else  {
        $(document.body).removeClass('mobile');
        $(document.body).removeClass('nobile');
    }
}

function heightAdjust() {
    if (!$('body.mobile').exists() && !$('body.nobile').exists() && $('#typing-quirks .replacementContainer').exists()) {
        leftHeight = $('#char_left').height();
        centerHeight = $('#char_center').height()-$('#typing-quirks .replacementContainer').height();
        $('#typing-quirks .replacementContainer').height(leftHeight-centerHeight);
    }
}

function unreadNotifications() {
    $.post('/chats/unread.json', function(data) {
        if (data.total!=0) {
            $('#unread-notifier').show().text(data.total+'!');
        } else {
            $('#unread-notifier').hide();
        }
    }, "json").complete(function() {
        if (logged_in) {
            window.setTimeout(unreadNotifications, 60000);
        }
    });
}

$(document).ready(function() {
    var quote = quotes[Math.floor(Math.random()*quotes.length)];
    $('#quote').html(quote);

    if(navigator.userAgent.match(/(iPad|iPhone|iPod)/g) ? true : false) {
        $('meta[name=viewport]').attr('content', 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />');
    }
    
    /* Topbar Menu */
    $('#toptitle').click(function() {
        if ($('body.menu').exists()) {
            $(document.body).removeClass('menu');
        } else {
            $(document.body).addClass('menu');
        }
    });
    $('#topbar').on("mouseleave", function(){
        if ($('body.menu').exists()) {
            $(document.body).removeClass('menu');
        }
    });
});

$(window).load(function() {
    screenCheck();
    heightAdjust();
    $(window).resize(function() {
        screenCheck();
        heightAdjust();
    });
});