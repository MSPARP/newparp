var ORIGINAL_TITLE = document.title;
var current_mode;
var shown_topics = {};

function unreadNotifications() {
    var chats_url = document.URL+".json";
    if (document.URL.substring(document.URL.length-1) == '/') {
        chats_url = document.URL.substring(0,document.URL.length-1)+".json";
    }
    $.getJSON(chats_url, function(data) {
        chats = data.chats;
        chatsUpdate(true);
    }).complete(function() {
        window.setTimeout(unreadNotifications, 10000);
    });
}

function fillColumn(column,numCols) {
    $('<div>').addClass('section').prop('id', 'column-'+column).appendTo('#under-page');
    for(var i=column; i<chats.length; i+=numCols) {
        chat = chats[i];
        $('<div>').addClass('card chat').prop('id', 'chat-'+chat.url.replace(/\//g,'-')).appendTo('#column-'+column);
        $('<a>').addClass('title').prop('href','/'+chat.url).text(chat.title+(chat.unread ? ' (unread)' : '')).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
        if (chat.online > 0) {
            $('<div>').addClass('users-online').text(chat.online+' online').appendTo('#chat-'+chat.url.replace(/\//g,'-').replace(/\//g,'-'));
        }
        if (chat.type == 'group') {
            if (shown_topics['chat-'+chat.url.replace(/\//g,'-').replace(/\//g,'-')]) {
                $('<div>').addClass('topic').html(bbEncode(chat.topic)).appendTo('#chat-'+chat.url.replace(/\//g,'-')).show();
            } else {
                $('<div>').addClass('topic').html(bbEncode(chat.topic)).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
            }
            $('<div>').addClass('line-behind-wrapper hide-topic').appendTo('#chat-'+chat.url.replace(/\//g,'-'));
            $('<div>').addClass('line-behind').appendTo('#chat-'+chat.url.replace(/\//g,'-')+' .line-behind-wrapper');
            $('<div>').addClass('text').html("Show Topic").appendTo('#chat-'+chat.url.replace(/\//g,'-')+' .line-behind-wrapper');
        }
    }
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
    if (current_mode == mode || first) {
        $('#under-page').empty();
        if ($('body.mobile').length>0) {
            fillColumn(1, 1);
        } else if ($('body.nobile').length>0) {
            fillColumn(1, 2);
            fillColumn(2, 2);
        } else {
            fillColumn(1, 3);
            fillColumn(2, 3);
            fillColumn(3, 3);
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

$('.section .chat .line-behind-wrapper').on('click', function (){
    if ($(this).parent().find('.topic').is(':visible')) {
        $(this).parent().find('.topic').hide();
        $(this).find('.text').html('Show Topic');
        shown_topics[$(this).parent().prop('id')] = false; 
    } else {
        $(this).parent().find('.topic').show();
        $(this).find('.text').html('Hide Topic');
        shown_topics[$(this).parent().prop('id')] = true;
    }
});

$(window).resize(function () {
    screenCheck();
    chatsUpdate();
});