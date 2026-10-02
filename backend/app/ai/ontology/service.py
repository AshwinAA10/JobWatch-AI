"""SkillOntologyService providing deterministic skill normalization, alias resolution, and relationship graph traversal."""

from typing import Dict, List, Optional, Set, Tuple
from app.ai.ontology.models import CORE_ONTOLOGY_DATA, SkillNode


class SkillOntologyService:
    """In-memory high performance graph for skill normalization, aliases, and transferability analysis."""

    def __init__(self, data: Optional[List[Dict]] = None) -> None:
        self.nodes: Dict[str, SkillNode] = {}
        self.alias_map: Dict[str, str] = {}  # lower_cased_alias -> canonical_name
        self._load_ontology(data or CORE_ONTOLOGY_DATA)

    def _load_ontology(self, data: List[Dict]) -> None:
        for entry in data:
            canonical = entry["canonical_name"]
            node = SkillNode(
                canonical_name=canonical,
                category=entry.get("category", "General"),
                aliases=set(entry.get("aliases", [])),
                transferable_to=dict(entry.get("transferable_to", {})),
                related_skills=set(entry.get("related", [])),
            )
            self.nodes[canonical] = node
            
            # Map canonical name itself (case-insensitive)
            self.alias_map[canonical.lower()] = canonical
            # Map aliases
            for alias in node.aliases:
                self.alias_map[alias.lower()] = canonical

    def normalize_skill(self, skill_name: str) -> str:
        """Resolve a raw skill string to its canonical ontology name if recognized.
        
        Examples:
            'js' -> 'JavaScript'
            'Postgres' -> 'PostgreSQL'
            'k8s' -> 'Kubernetes'
            'custom_tech' -> 'Custom_tech' (clean title fallback)
        """
        if not skill_name or not skill_name.strip():
            return ""

        clean = skill_name.strip()
        lower = clean.lower()

        if lower in self.alias_map:
            return self.alias_map[lower]

        # Handle common punctuation / version suffix cleanup (e.g. "React.js" -> "React")
        simplified = lower.replace(".", "").replace("-", " ")
        if simplified in self.alias_map:
            return self.alias_map[simplified]

        # Return standardized title capitalization if not in curated dictionary
        return clean.title() if len(clean) > 3 else clean.upper()

    def normalize_skills(self, skills: List[str]) -> List[str]:
        """Normalize a list of skill names and remove duplicates while preserving order."""
        seen: Set[str] = set()
        normalized: List[str] = []
        for s in skills:
            norm = self.normalize_skill(s)
            if norm and norm.lower() not in seen:
                seen.add(norm.lower())
                normalized.append(norm)
        return normalized

    def find_transferable_skills(
        self,
        candidate_skills: List[str],
        target_skills: List[str],
        min_transfer_weight: float = 0.70,
    ) -> List[Dict[str, any]]:
        """Identify which candidate skills transfer to fulfill target job requirements."""
        norm_candidate = self.normalize_skills(candidate_skills)
        norm_target = self.normalize_skills(target_skills)
        cand_set = set(norm_candidate)

        transferable_matches: List[Dict[str, any]] = []

        for target in norm_target:
            # If already an exact match, skip (exact match handled by rule/direct match)
            if target in cand_set:
                continue

            best_source: Optional[str] = None
            best_weight: float = 0.0

            for cand_skill in norm_candidate:
                # 1. Direct transferability from ontology
                node = self.nodes.get(cand_skill)
                if node and target in node.transferable_to:
                    weight = node.transferable_to[target]
                    if weight > best_weight:
                        best_weight = weight
                        best_source = cand_skill

                # 2. Reverse check: does target list candidate as transferable source
                target_node = self.nodes.get(target)
                if target_node and cand_skill in target_node.transferable_to:
                    weight = target_node.transferable_to[cand_skill]
                    if weight > best_weight:
                        best_weight = weight
                        best_source = cand_skill

            if best_source and best_weight >= min_transfer_weight:
                transferable_matches.append({
                    "target_skill": target,
                    "matched_via": best_source,
                    "transfer_weight": round(best_weight, 2),
                    "relationship": "TRANSFERABLE",
                })

        return transferable_matches

    def analyze_skill_gaps(
        self,
        candidate_skills: List[str],
        required_skills: List[str],
        preferred_skills: Optional[List[str]] = None,
    ) -> Dict[str, any]:
        """Perform comprehensive skill gap analysis distinguishing exact, transferable, and missing skills."""
        norm_candidate = set(self.normalize_skills(candidate_skills))
        norm_required = self.normalize_skills(required_skills)
        norm_preferred = self.normalize_skills(preferred_skills or [])

        # 1. Exact matches
        matched_required = [s for s in norm_required if s in norm_candidate]
        matched_preferred = [s for s in norm_preferred if s in norm_candidate]

        # 2. Remaining unmet skills
        unmet_required = [s for s in norm_required if s not in norm_candidate]
        unmet_preferred = [s for s in norm_preferred if s not in norm_candidate]

        # 3. Transferable checks
        transferable = self.find_transferable_skills(list(norm_candidate), unmet_required + unmet_preferred)
        transferable_targets = {t["target_skill"]: t for t in transferable}

        # 4. Final classification
        final_missing_required: List[str] = []
        final_transferable_required: List[Dict] = []
        for req in unmet_required:
            if req in transferable_targets:
                final_transferable_required.append(transferable_targets[req])
            else:
                final_missing_required.append(req)

        final_missing_preferred: List[str] = []
        for pref in unmet_preferred:
            if pref not in transferable_targets:
                final_missing_preferred.append(pref)

        total_req = len(norm_required)
        req_coverage = (
            round((len(matched_required) + 0.5 * len(final_transferable_required)) / total_req, 2)
            if total_req > 0 else 1.0
        )

        return {
            "matched_required": matched_required,
            "matched_preferred": matched_preferred,
            "transferable_matches": transferable,
            "missing_required": final_missing_required,
            "missing_preferred": final_missing_preferred,
            "required_coverage": req_coverage,
        }


# Global singleton instance
skill_ontology = SkillOntologyService()
