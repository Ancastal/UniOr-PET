# How the new version works

---

The project manager through the management interface assigns a project to a given registered translator, specifying e-mail address, source and target languages, source text and MT output to post-edit.
The translator receives an e-mail to accept the job: LINK -> REST API -> MONGODB UPDATE QUERY
The translator logs in and finds the source text and MT output, assigned by the project manager.

```
project_manager {
  name: str;
  surname: str;
  email_address: str;
  projects: ARRAY[project]
}
```

```
project {
    src_lang: str;
    tgt_lang: str;
    accepted_date: DATETIME;
    docs: {
      src_text: ARRAY[str];
      mt_output: ARRAY[str];
    }
    translators: ARRAY[translator]
}
```

```
translator {
    name: str;
    surname: str;
    email_address: str;
    assigned_project: ARRAY[project];
}
```
