$(function(){
    $('.block-container').each(function() {
        var margin = ($(this).height() - $(this).find('.block').height())/2;
        $(this).find('.block').css('margin-top',margin);
        if ($(this).find('.description').length !== 0) {
            $(this).addClass('has-description');
        }
    });
    $('logo').each(function() {
        $(this).css('background-image','url(/static/img/root-icons/'+$(this).prop('class')+'.png)');
    });
    $('.block-container').on('click', function() {
        $('.block-container').each(function(){
            $(this).removeClass('selected');
        });
        if ($(this).find('.description').length !== 0) {
            $(this).addClass('selected');
            $('.block-container').each(function(){
                if ($(this).hasClass('selected')) {
                    $(this).find('.block, .description').stop().slideToggle();
                } else {
                    if ($(this).find('.description:visible').length !== 0) {
                        $(this).find('.block, .description').stop().slideToggle();
                    }
                }
            });
        }
    });
});