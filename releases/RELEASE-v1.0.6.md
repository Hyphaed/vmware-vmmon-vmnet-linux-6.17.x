# Release v1.0.6 - Use Semver to Identify Kernel Version Components

**Release Date:** November 18, 2025

---

## ⭐ What's New

The internal code used to identify available kernel versions has been replaced with the Python semver package.
Previously, not any variant of plus and minus symbols has been identified properly and could break identification such as `6.16.3+deb13-amd64`
which is an example for Debian kernels when using backports.

---

## 🎯 Important

If you have already used this software, you must manually delete the directory that stores all the dependencies before performing any other tasks:

`rm -r ~/.miniforge3`


## 🎯 Usage Examples

Because only internal code has been changed, all descriptions from Release v1.0.5 apply.

## 🐛 Known Issues

None reported.

---

## 🙏 Feedback

If you encounter any issues with the system optimizer or have suggestions for additional optimizations, please open an issue on GitHub:

https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/issues

---

## 📈 Version History

- **v1.0.6** (November 18, 2025) - Using Python semver
- **v1.0.5** (October  17, 2025) - System Optimizer integration
- **v1.0.4** (October  16, 2025) - Python wizard improvements
- **v1.0.3** (October  15, 2025) - Multi-kernel support
- **v1.0.2** (October  14, 2025) - Hardware detection engine
- **v1.0.1** (October  13, 2025) - Initial release

---

**Enjoy your optimized VMware Workstation experience! 🚀**

