The **original source code** is usually only in the developer’s project folder, for example:

```bash
MyApp/
├── MyApp.xcodeproj
├── MyApp/
│   ├── AppDelegate.swift
│   ├── ContentView.swift
│   └── ViewController.swift
```

A built macOS app only contains the compiled executable here:

```bash
MyApp.app/Contents/MacOS/MyApp
```

That file contains **machine code**, not the original `.swift`, `.m`, `.mm`, `.cpp`, or `.h` files.

You can check what is inside an app with:

```bash
find MyApp.app -type f
```

Sometimes you may find resources here:

```bash
MyApp.app/Contents/Resources/
```

But source code is normally **not included** unless the developer accidentally bundled it.
