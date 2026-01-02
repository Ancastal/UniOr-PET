mkdir -p ~/.streamlit/

echo "\
[general]\n\
email = \"antonio.castaldo@phd.unipi.it\"\n\
" > ~/.streamlit/credentials.toml

echo "\
[server]\n\
headless = true\n\
enableCORS = false\n\
port = \$PORT\n\
\n\
[client]\n\
toolbarMode = \"minimal\"\n\
\n\
[ui]\n\
hideTopBar = true\n\
" > ~/.streamlit/config.toml
