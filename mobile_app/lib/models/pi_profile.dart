class PIProfile {
  final int? id;
  final String name;
  final String institution;
  final int papersCount;
  final int hIndex;
  final String researchAreas;
  final String activeYears;
  final String? bio;
  final String? photoUrl;

  const PIProfile({
    this.id,
    required this.name,
    required this.institution,
    this.papersCount = 0,
    this.hIndex = 0,
    this.researchAreas = '',
    this.activeYears = '',
    this.bio,
    this.photoUrl,
  });

  Map<String, dynamic> toMap() {
    return {
      if (id != null) 'id': id,
      'name': name,
      'institution': institution,
      'papers_count': papersCount,
      'h_index': hIndex,
      'research_areas': researchAreas,
      'active_years': activeYears,
      'bio': bio,
      'photo_url': photoUrl,
    };
  }

  factory PIProfile.fromMap(Map<String, dynamic> map) {
    return PIProfile(
      id: map['id'] as int?,
      name: map['name'] as String,
      institution: map['institution'] as String? ?? '',
      papersCount: map['papers_count'] as int? ?? 0,
      hIndex: map['h_index'] as int? ?? 0,
      researchAreas: map['research_areas'] as String? ?? '',
      activeYears: map['active_years'] as String? ?? '',
      bio: map['bio'] as String?,
      photoUrl: map['photo_url'] as String?,
    );
  }

  PIProfile copyWith({
    int? id,
    String? name,
    String? institution,
    int? papersCount,
    int? hIndex,
    String? researchAreas,
    String? activeYears,
    String? bio,
    String? photoUrl,
  }) {
    return PIProfile(
      id: id ?? this.id,
      name: name ?? this.name,
      institution: institution ?? this.institution,
      papersCount: papersCount ?? this.papersCount,
      hIndex: hIndex ?? this.hIndex,
      researchAreas: researchAreas ?? this.researchAreas,
      activeYears: activeYears ?? this.activeYears,
      bio: bio ?? this.bio,
      photoUrl: photoUrl ?? this.photoUrl,
    );
  }
}
