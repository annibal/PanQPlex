#!/bin/sh

if [ -n "$VISUAL" ]; then
  exec $VISUAL "$HOME/.config/n2bl/client_secret.json"
elif [ -n "$EDITOR" ]; then
  exec $EDITOR "$HOME/.config/n2bl/client_secret.json"
elif type sensible-editor >/dev/null 2>/dev/null; then
  exec sensible-editor "$HOME/.config/n2bl/client_secret.json"
elif cmd=$(xdg-mime query default ) 2>/dev/null; [ -n "$cmd" ]; then
  exec "$cmd" "$HOME/.config/n2bl/client_secret.json"
else
  editors='code nano joe vi'
  if [ -n "$DISPLAY" ]; then
    editors="gedit kate $editors"
  fi
  for x in $editors; do
    if type "$x" >/dev/null 2>/dev/null; then
      exec "$x" "$HOME/.config/n2bl/client_secret.json"
    fi
  done
fi