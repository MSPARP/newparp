var ORIGINAL_TITLE = document.title;
var current_mode;

function unreadNotifications() {
    var chats_url = document.URL+".json";
    if (document.URL.substring(document.URL.length-1) == '/') {
        chats_url = document.URL.substring(0,document.URL.length-1)+".json";
    }
    $.getJSON(chats_url, function(data) {
        var chats = data.chats;
        chatsUpdate(true);
    }).complete(function() {
        window.setTimeout(unreadNotifications, 10000);
    });
}

function chatsUpdate(first) {
    if ($('body').prop('class')) {
        mode = $('body').prop('class');
    } else {
        mode = 'none';
    }
    
    unread_chats = 0;
    for (i in chats) {
        chat = chats[i];
        if (chat.unread) {
            unread_chats++;
        }
    }
    if (unread_chats > 0) {
        document.title = unread_chats+" unread - "+ORIGINAL_TITLE;
    } else {
        document.title = ORIGINAL_TITLE;
    }
    console.log("test");
    if (current_mode == mode || first) {
        console.log(mode);
        $('#under-page').empty();
        if ($('body.mobile').length>0) {
            $('<div>').addClass('section').prop('id', 'column-1').appendTo('#under-page');
            for(i in chats) {
                chat = chats[i];
                $('<div>').addClass('card chat').prop('id', 'chat-'+chat.url.replace(/\//g,'-')).appendTo('#column-1');
                $('<a>').addClass('title').prop('href','/'+chat.url).text(chat.title+(chat.unread ? ' (unread)' : '')).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                if (chat.online > 0) {
                    $('<div>').addClass('users-online').text(chat.online+' online').appendTo('#chat-'+chat.url.replace(/\//g,'-').replace(/\//g,'-'));
                }
                if (chat.type == 'group') {
                    $('<div>').addClass('topic').html(bbEncode(chat.topic)).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                }
            }
        } else if ($('body.nobile').length>0) {
            $('<div>').addClass('section').prop('id', 'column-1').appendTo('#under-page');
            $('<div>').addClass('section').prop('id', 'column-2').appendTo('#under-page');
            for (var i=0; i<chats.length; i+=2) {
                chat = chats[i];
                $('<div>').addClass('card chat').prop('id', 'chat-'+chat.url.replace(/\//g,'-')).appendTo('#column-1');
                $('<a>').addClass('title').prop('href','/'+chat.url).text(chat.title+(chat.unread ? ' (unread)' : '')).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                if (chat.online > 0) {
                    $('<div>').addClass('users-online').text(chat.online+' online').appendTo('#chat-'+chat.url.replace(/\//g,'-').replace(/\//g,'-'));
                }
                if (chat.type == 'group') {
                    $('<div>').addClass('topic').html(bbEncode(chat.topic)).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                }
            }
            for (var i=1; i<chats.length; i+=2) {
                chat = chats[i];
                $('<div>').addClass('card chat').prop('id', 'chat-'+chat.url.replace(/\//g,'-')).appendTo('#column-2');
                $('<a>').addClass('title').prop('href','/'+chat.url).text(chat.title+(chat.unread ? ' (unread)' : '')).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                if (chat.online > 0) {
                    $('<div>').addClass('users-online').text(chat.online+' online').appendTo('#chat-'+chat.url.replace(/\//g,'-').replace(/\//g,'-'));
                }
                if (chat.type == 'group') {
                    $('<div>').addClass('topic').html(bbEncode(chat.topic)).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                }
            }
        } else {
            $('<div>').addClass('section').prop('id', 'column-1').appendTo('#under-page');
            $('<div>').addClass('section').prop('id', 'column-2').appendTo('#under-page');
            $('<div>').addClass('section').prop('id', 'column-3').appendTo('#under-page');
            for (var i=0; i<chats.length; i+=3) {
                chat = chats[i];
                $('<div>').addClass('card chat').prop('id', 'chat-'+chat.url.replace(/\//g,'-')).appendTo('#column-1');
                $('<a>').addClass('title').prop('href','/'+chat.url).text(chat.title+(chat.unread ? ' (unread)' : '')).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                if (chat.online > 0) {
                    $('<div>').addClass('users-online').text(chat.online+' online').appendTo('#chat-'+chat.url.replace(/\//g,'-').replace(/\//g,'-'));
                }
                if (chat.type == 'group') {
                    $('<div>').addClass('topic').html(bbEncode(chat.topic)).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                }
            }
            for (var i=1; i<chats.length; i+=3) {
                chat = chats[i];
                $('<div>').addClass('card chat').prop('id', 'chat-'+chat.url.replace(/\//g,'-')).appendTo('#column-2');
                $('<a>').addClass('title').prop('href','/'+chat.url).text(chat.title+(chat.unread ? ' (unread)' : '')).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                if (chat.online > 0) {
                    $('<div>').addClass('users-online').text(chat.online+' online').appendTo('#chat-'+chat.url.replace(/\//g,'-').replace(/\//g,'-'));
                }
                if (chat.type == 'group') {
                    $('<div>').addClass('topic').html(bbEncode(chat.topic)).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                }
            }
            for (var i=2; i<chats.length; i+=3) {
                chat = chats[i];
                $('<div>').addClass('card chat').prop('id', 'chat-'+chat.url.replace(/\//g,'-')).appendTo('#column-3');
                $('<a>').addClass('title').prop('href','/'+chat.url).text(chat.title+(chat.unread ? ' (unread)' : '')).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                if (chat.online > 0) {
                    $('<div>').addClass('users-online').text(chat.online+' online').appendTo('#chat-'+chat.url.replace(/\//g,'-').replace(/\//g,'-'));
                }
                if (chat.type == 'group') {
                    $('<div>').addClass('topic').html(bbEncode(chat.topic)).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                }
            }
        }
    }
    
    if ($('#column-1').is(':empty')) {
        $('#column-1').remove();
    }
    if ($('#column-2').is(':empty')) {
        $('#column-2').remove();
    }
    if ($('#column-3').is(':empty')) {
        $('#column-3').remove();
    }
    if ($('#under-page').is(':empty')) {
        $('#under-page').html('<div class="section"> </div>');
    }
    current_mode = mode;
}

$(function(){
    screenCheck();

    if ($('body').prop('class')) {
        current_mode = $('body').prop('class');
    } else {
        current_mode = 'none';
    }
    
    chatsUpdate(true);
    setTimeout(unreadNotifications, 10000)
});

$(window).resize(function () {
    screenCheck();
    chatsUpdate();
});