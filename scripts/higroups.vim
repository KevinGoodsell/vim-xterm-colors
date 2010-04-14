
function! ShowHiGroups()
    redir => hitext
    silent highlight
    redir END

    let hitext = substitute(hitext,
                           \'\v(\w|\s)*( links to | xxx cleared)(\w|\s)*\n?',
                           \'', 'g')
    let hilines = split(hitext, '\n')

    for line in hilines
        let group = matchstr(line, '\v^\w+')
        exec 'syntax match ' . group . ' /\v^' . group . ' +\zsxxx\ze/'
    endfor
    call append(0, hilines)
endfunction

" Somo of this is borrowed from hitest.vim:

" Open a new window if the current one isn't empty
if line("$") != 1 || getline(1) != ""
  new
endif

" edit temporary file
edit Highlight\ groups

call ShowHiGroups()

set nomodified
normal gg
