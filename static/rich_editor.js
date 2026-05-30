(function () {
    function bindEditor(root) {
        const content = root.querySelector('.rich-content');
        const hidden = root.querySelector('input[type="hidden"]');
        const buttons = root.querySelectorAll('button[data-cmd]');
        const selects = root.querySelectorAll('select[data-cmd]');

        if (!content || !hidden) {
            return;
        }

        function sync() {
            hidden.value = content.innerHTML.trim();
        }

        buttons.forEach((btn) => {
            btn.addEventListener('click', () => {
                const cmd = btn.getAttribute('data-cmd');
                if (!cmd) {
                    return;
                }
                document.execCommand(cmd, false);
                content.focus();
                sync();
            });
        });

        selects.forEach((select) => {
            select.addEventListener('change', () => {
                const cmd = select.getAttribute('data-cmd');
                if (!cmd) {
                    return;
                }
                document.execCommand(cmd, false, select.value);
                content.focus();
                sync();
            });
        });

        content.addEventListener('input', sync);
        sync();
    }

    function bindLetterEditor() {
        const wrapper = document.querySelector('[data-letter-editor]');
        if (!wrapper) {
            return;
        }
        const content = wrapper.querySelector('.rich-content');
        const hidden = wrapper.querySelector('input[name="content_html"]');
        const buttons = wrapper.querySelectorAll('button[data-cmd]');
        const selects = wrapper.querySelectorAll('select[data-cmd]');
        if (!content || !hidden) {
            return;
        }

        function sync() {
            hidden.value = content.innerHTML.trim();
        }

        buttons.forEach((btn) => {
            btn.addEventListener('click', () => {
                const cmd = btn.getAttribute('data-cmd');
                if (!cmd) {
                    return;
                }
                document.execCommand(cmd, false);
                content.focus();
                sync();
            });
        });

        selects.forEach((select) => {
            select.addEventListener('change', () => {
                const cmd = select.getAttribute('data-cmd');
                if (!cmd) {
                    return;
                }
                document.execCommand(cmd, false, select.value);
                content.focus();
                sync();
            });
        });

        content.addEventListener('input', sync);
        sync();
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.rich-editor').forEach(bindEditor);
        bindLetterEditor();

        document.querySelectorAll('form').forEach((form) => {
            form.addEventListener('submit', () => {
                form.querySelectorAll('.rich-editor').forEach((editor) => {
                    const content = editor.querySelector('.rich-content');
                    const hidden = editor.querySelector('input[type="hidden"]');
                    if (content && hidden) {
                        hidden.value = content.innerHTML.trim();
                    }
                });

                const letterContent = form.hasAttribute('data-letter-editor')
                    ? form.querySelector('.rich-content')
                    : null;
                const letterHidden = form.querySelector('input[name="content_html"]');
                if (letterContent && letterHidden) {
                    letterHidden.value = letterContent.innerHTML.trim();
                }
            });
        });
    });
})();
