function getTimestamp(seconds_from_epoch) {
    var month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun","Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    var timestamp = new Date(seconds_from_epoch*1000);
    return month_names[timestamp.getMonth()]+' '+timestamp.getDate()+' '+(timestamp.getHours()===0?'0':'')+timestamp.getHours()+':'+(timestamp.getMinutes()<10?'0':'')+timestamp.getMinutes();
}

$(function(){
    $('#archiveConversation span').each(function() {
        var line = bbEncode($(this).find('.message').text());
        $(this).find('.message').html(line);
        $(this).find('.info .right .post_timestamp').text(getTimestamp($(this).find('.info .right .post_timestamp').text()));
    });
});