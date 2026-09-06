# Extracted unchanged method; see provenance.json and LICENSE.
def _list_skills_in_repo(self, repo: str, path: str) -> List[SkillMeta]:
        """List skill directories in a GitHub repo path, using cached index."""
        cache_key = f"{repo}_{path}".replace("/", "_").replace(" ", "_")
        cached = _cached_metas(cache_key)
        if cached is not None:
            return cached
        resp = self._github_get(f"{_API}/{repo}/contents/{path.rstrip('/')}")
        if resp is None or resp.status_code != 200:
            return []
        entries = resp.json()
        if not isinstance(entries, list):
            return []
        skills: List[SkillMeta] = []
        groupings = self._get_skillsh_groupings(repo)
        prefix = path.rstrip("/")
        for entry in entries:
            if entry.get("type") != "dir" or entry["name"].startswith((".", "_")):
                continue
            dir_name = entry["name"]
            meta = self.inspect(f"{repo}/{prefix}/{dir_name}" if prefix else f"{repo}/{dir_name}")
            if meta:
                category = groupings and (groupings.get(meta.name) or groupings.get(dir_name))
                if category:
                    meta.extra["category"] = category
                skills.append(meta)
        _cache_metas(cache_key, skills)
        return skills
