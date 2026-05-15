# Open Source License Audit

| Component | Purpose | License | Type |
|----------|--------|--------|------|
| React | Frontend UI library | MIT | Permissive |
| Express | Backend framework | MIT | Permissive |
| Axios | HTTP client | MIT | Permissive |
| SQLite | Database | Public Domain | Permissive |
| Tailwind CSS | Styling | MIT | Permissive |

## Conclusion

All selected libraries use permissive licenses, meaning there are **no major legal restrictions** on using, modifying, or distributing this project.


## Mission Logger Component

### Provides Interface
- logCommand(user, action, status)
- getLogs()
- exportLogs(format)

### Requires Interface
- Database connection (to store logs)
- System clock (to generate timestamps)