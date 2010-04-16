
function! ShowHiGroups(keeplinks)
    redir => hitext
    silent highlight
    redir END

    let hitext = substitute(hitext, '\v(\w|\s)* xxx cleared(\w|\s)*\n?',
                           \'', 'g')
    if !a:keeplinks
        let hitext = substitute(hitext, '\v(\w|\s)* links to (\w|\s)*\n?',
                               \'', 'g')
    endif
    let hilines = split(hitext, '\n')

    for line in hilines
        let group = matchstr(line, '\v^\zs\w+\ze\s+xxx')
        if strlen(group) > 0
            exec 'syntax match ' . group . ' /\v^' . group . ' +\zsxxx\ze/'
        endif
    endfor
    call append(0, hilines)
endfunction

" Somo of this is borrowed from hitest.vim:

" Open a new window if the current one isn't empty
if line("$") != 1 || getline(1) != ""
    new
endif

" edit temporary file
exec 'edit ' . g:colors_name . '\ Highlight\ groups'

if exists('g:keeplinks')
    let s:keeplinks = g:keeplinks
else
    let s:keeplinks = 0
endif
call ShowHiGroups(s:keeplinks)

set nomodified
normal gg
