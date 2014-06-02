var current_mode;

function chatsUpdate(first) {
    $('#under-page').empty();
    
    if ($('body').addClass()) {
        mode = $('body').addClass();
    } else {
        mode = 'none';
    }
    
    if (current_mode == mode || first) {
        if ($('body.mobile').length>0) {
            $('</div>').addClass('section').prop('id', 'column-1').appendTo('#under-page');
            for(chat in chats) {
                $('</div>').addClass('card chat').prop('id', 'chat-'+chat.url).appendTo('#column-1');
                $('</a>').addClass('title').prop('href','/'+chat.url).text(chat.url+(chat.unread ? ' '+chat.url : '')).append('#column-1');
                if (chat.type == 'group') {
                    $('</div>').addClass('topic').text(chat.topic).appendTo('#column-1');
                }
            }
        } else if ($('body.nobile').length>0) {
            $('</div>').addClass('section').prop('id', 'column-1').appendTo('#under-page');
            $('</div>').addClass('section').prop('id', 'column-2').appendTo('#under-page');
            for (var i=0; i<chats.length; i+=2) {
                chat = chats[i];
                $('</div>').addClass('card chat').prop('id', 'chat-'+chat.url).appendTo('#column-1');
                $('</a>').addClass('title').prop('href','/'+chat.url).text(chat.url+(chat.unread ? ' '+chat.url : '')).append('#column-1');
                if (chat.type == 'group') {
                    $('</div>').addClass('topic').text(chat.topic).appendTo('#column-1');
                }
            }
            for (var i=1; i<chats.length; i+=2) {
                chat = chats[i];
                $('</div>').addClass('card chat').prop('id', 'chat-'+chat.url).appendTo('#column-2');
                $('</a>').addClass('title').prop('href','/'+chat.url).text(chat.url+(chat.unread ? ' '+chat.url : '')).append('#column-2');
                if (chat.type == 'group') {
                    $('</div>').addClass('topic').text(chat.topic).appendTo('#column-2');
                }
            }
        } else {
            $('</div>').addClass('section').prop('id', 'column-1').appendTo('#under-page');
            $('</div>').addClass('section').prop('id', 'column-2').appendTo('#under-page');
            $('</div>').addClass('section').prop('id', 'column-3').appendTo('#under-page');
            for (var i=0; i<chats.length; i+=3) {
                chat = chats[i];
                $('</div>').addClass('card chat').prop('id', 'chat-'+chat.url).appendTo('#column-1');
                $('</a>').addClass('title').prop('href','/'+chat.url).text(chat.url+(chat.unread ? ' '+chat.url : '')).append('#column-1');
                if (chat.type == 'group') {
                    $('</div>').addClass('topic').text(chat.topic).appendTo('#column-1');
                }
            }
            for (var i=1; i<chats.length; i+=3) {
                chat = chats[i];
                $('</div>').addClass('card chat').prop('id', 'chat-'+chat.url).appendTo('#column-2');
                $('</a>').addClass('title').prop('href','/'+chat.url).text(chat.url+(chat.unread ? ' '+chat.url : '')).append('#column-2');
                if (chat.type == 'group') {
                    $('</div>').addClass('topic').text(chat.topic).appendTo('#column-2');
                }
            }
            for (var i=2; i<chats.length; i+=3) {
                chat = chats[i];
                $('</div>').addClass('card chat').prop('id', 'chat-'+chat.url).appendTo('#column-3');
                $('</a>').addClass('title').prop('href','/'+chat.url).text(chat.url+(chat.unread ? ' '+chat.url : '')).append('#column-3');
                if (chat.type == 'group') {
                    $('</div>').addClass('topic').text(chat.topic).appendTo('#column-3');
                }
            }
        }
    }
    current_mode = mode;
}

$(function(){
    if ($('body').addClass()) {
        current_mode = $('body').addClass();
    } else {
        current_mode = 'none';
    }
    
    chatsUpdate(true);
});